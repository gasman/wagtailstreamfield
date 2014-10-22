from six import with_metaclass

from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django.forms import MediaDefiningClass, Media

class Block(with_metaclass(MediaDefiningClass)):
    def html_declarations(self, definition_prefix):
        return ''

    def js_initializer(self, definition_prefix):
        """
        Returns a Javascript expression that evaluates to a function.
        This will be called (passing the element prefix to it) whenever a block is created,
        to initialise any javascript behaviours required by the block.

        If no JS behaviour is required, this method can return None instead.
        """
        return None

    def __call__(self, *args, **kwargs):
        try:
            value = args[0]
        except IndexError:
            value = self.default  # constructor must set this
        prefix = kwargs.get('prefix', '')
        return self.BoundBlock(self, prefix, value)


class BaseBoundBlock(object):
    def __init__(self, definition, prefix, value):
        self.definition = definition
        self.prefix = prefix
        self.value = value


class TextInput(Block):
    def __init__(self, **kwargs):
        self.label = kwargs['label']
        self.default = kwargs.get('default', '')

    class BoundBlock(BaseBoundBlock):
        def render(self):
            return format_html(
                """<label for="{0}">{1}</label> <input type="text" name="{2}" id="{3}" value="{4}">""",
                self.prefix, self.definition.label, self.prefix, self.prefix, self.value
            )


class Chooser(Block):
    def __init__(self, **kwargs):
        self.label = kwargs['label']
        self.default = kwargs.get('default', '')

    class Media:
        js = ['js/blocks/chooser.js']

    def js_initializer(self, definition_prefix):
        return "Chooser('%s')" % definition_prefix

    class BoundBlock(BaseBoundBlock):
        def render(self):
            return format_html(
                """<label>{0}</label> <input type="button" id="{1}-button" value="Choose a thing">""",
                self.definition.label, self.prefix
            )


class StructBlock(Block):
    def __init__(self, child_defs, **kwargs):
        self.child_defs = child_defs
        self.default = kwargs.get('default', {})

    def html_declarations(self, definition_prefix):
        return format_html_join('\n', '{0}', [
            (child_def.html_declarations("%s-%s" % (definition_prefix, name)),)
            for (name, child_def) in self.child_defs
        ])

    def js_initializer(self, definition_prefix):
        child_initializers = []
        for (name, child_def) in self.child_defs:
            initializer_js = child_def.js_initializer("%s-%s" % (definition_prefix, name))
            if initializer_js:
                child_initializers.append((name, initializer_js))

        if child_initializers:  # don't bother to output a js initializer if children don't require one
            initializer_js_list = [
                "['%s', %s]" % (name, initializer_js)
                for name, initializer_js in child_initializers
            ]
            return "StructBlock([\n%s\n])" % ',\n'.join(initializer_js_list)

    @property
    def media(self):
        media = Media(js=['js/blocks/struct.js'])
        for name, item in self.child_defs:
            media += item.media
        return media

    class BoundBlock(BaseBoundBlock):
        def __init__(self, definition, prefix, value):
            super(StructBlock.BoundBlock, self).__init__(definition, prefix, value)
            self.children = [
                child_def(self.value.get(name, child_def.default), prefix="%s-%s" % (self.prefix, name))
                for (name, child_def) in self.definition.child_defs
            ]

        def render(self):
            list_items = format_html_join('\n', "<li>{0}</li>", [(c.render(),) for c in self.children])
            return format_html("<ul>{0}</ul>", list_items)


class ListBlock(Block):
    def __init__(self, child_def, **kwargs):
        self.child_def = child_def
        self.default = kwargs.get('default', [])
        self.label = kwargs.get('label', '')
        self.template_child = self.child_def(prefix="__PREFIX__")

    def html_declarations(self, definition_prefix):
        template_declaration = format_html(
            '<script type="text/template" id="{0}-template">{1}</script>',
            definition_prefix, self.template_child.render()
        )
        child_declarations = self.child_def.html_declarations("%s-item" % definition_prefix)
        return mark_safe(template_declaration + child_declarations)

    def js_initializer(self, definition_prefix):
        child_initializer = self.child_def.js_initializer("%s-item" % definition_prefix)
        if child_initializer:
            return "ListBlock('%s', %s)" % (definition_prefix, child_initializer)
        else:
            return "ListBlock('%s')" % (definition_prefix)

    @property
    def media(self):
        return Media(js=['js/blocks/list.js']) + self.child_def.media

    class BoundBlock(BaseBoundBlock):
        def __init__(self, definition, prefix, value):
            super(ListBlock.BoundBlock, self).__init__(definition, prefix, value)

            self.children = [
                self.definition.child_def(child_val, prefix="%s-%d" % (self.prefix, i))
                for (i, child_val) in enumerate(self.value)
            ]

        def render(self):
            return render_to_string('core/blocks/list.html', {
                'label': self.definition.label,
                'self': self,
            })


class StreamBlock(Block):
    def __init__(self, child_defs, **kwargs):
        self.child_defs = child_defs
        self.default = kwargs.get('default', [])
        self.label = kwargs.get('label', '')

        self.child_defs_by_name = {}
        self.template_children = {}
        for name, child_def in self.child_defs:
            self.child_defs_by_name[name] = child_def
            self.template_children[name] = child_def(prefix="__PREFIX__")

    def html_declarations(self, definition_prefix):
        child_def_declarations = [
            format_html(
                """
                    {html_declarations}
                    <script type="text/template" id="{definition_prefix}-template-{child_name}">
                        {child_template}
                    </script>
                """,
                html_declarations=child_def.html_declarations("%s-child-%s" % (definition_prefix, name)),
                definition_prefix=definition_prefix,
                child_name=name,
                child_template=self.template_children[name].render()
            )
            for (name, child_def) in self.child_defs
        ]

        return mark_safe('\n'.join(child_def_declarations))

    def js_initializer(self, definition_prefix):
        child_js_defs = [
            """{{
                'name': '{child_name}',
                'initializer': {initializer}
            }}""".format(
                child_name=name,
                initializer=child_def.js_initializer("%s-child-%s" % (definition_prefix, name)) or 'null'
            )
            for name, child_def in self.child_defs
        ]

        return "StreamBlock([\n%s\n])" % ',\n'.join(child_js_defs)

    @property
    def media(self):
        media = Media(js=['js/blocks/stream.js'])
        for name, item in self.child_defs:
            media += item.media
        return media

    class BoundBlock(BaseBoundBlock):
        def __init__(self, definition, prefix, value):
            super(StreamBlock.BoundBlock, self).__init__(definition, prefix, value)
            self.child_records = []  # tuple of index, type, block object

            index = 0
            for item in value:
                child_def = definition.child_defs_by_name.get(item['type'])
                if child_def:
                    child_block = child_def(item['value'], prefix="%s-%d-item" % (self.prefix, index))
                    self.child_records.append((index, item['type'], child_block))
                    index += 1

        def render(self):
            return render_to_string('core/blocks/stream.html', {
                'label': self.definition.label,
                'self': self,
            })
