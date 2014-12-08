import re

from six import with_metaclass

from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.template.loader import render_to_string
from django.forms import MediaDefiningClass, Media

# helpers for Javascript expression formatting

def indent(string, depth=1):
    """indent all non-empty lines of string by 'depth' 4-character tabs"""
    return re.sub(r'(^|\n)([^\n]+)', '\g<1>' + ('    ' * depth) + '\g<2>', string)

def js_dict(d):
    """
    Return a Javascript expression string for the dict 'd'.
    Keys are assumed to be strings consisting only of JS-safe characters, and will be quoted but not escaped;
    values are assumed to be valid Javascript expressions and will be neither escaped nor quoted (but will be
    wrapped in parentheses, in case some awkward git decides to use the comma operator...)
    """
    dict_items = [
        indent("'%s': (%s)" % (k, v))
        for (k, v) in d.items()
    ]
    return "{\n%s\n}" % ',\n'.join(dict_items)

# =========================================
# Top-level superclasses and helper objects
# =========================================

class BlockOptions(object):
    def __init__(self, **kwargs):
        # standard options are 'label' and 'default'
        self.label = kwargs.get('label')

        try:
            self.default = kwargs['default']
        except KeyError:
            # subclasses are expected to set a default at the class level, so that if default
            # is not passed in the constructor (NB this is distinct from passing default=None)
            # then we'll revert to the block type's own default instead.
            pass

class BlockFactory(with_metaclass(MediaDefiningClass)):
    def __init__(self, block_options, name=None, definition_prefix=''):
        self.block_options = block_options
        self.name = name
        self.definition_prefix = definition_prefix

        self.default = self.block_options.default

        # Try to get a field label from block_options, or failing that, generate one from name
        self.label = getattr(block_options, 'label', None)
        if self.label is None and self.name is not None:
            self.label = capfirst(self.name.replace('_', ' '))

    def html_declarations(self):
        """
        Return an HTML fragment to be rendered on the page once per block definition -
        as opposed to once per occurrence of the block. For example, the block definition
            ListBlock(label="Shopping list", TextInput(label="Product"))
        needs to output a <script type="text/template"></script> block containing the HTML for
        a 'product' text input, to that these can be dynamically added to the list. This
        template block must only occur once in the page, even if there are multiple 'shopping list'
        blocks on the page.

        Any element IDs used in this HTML fragment must begin with definition_prefix.
        (More precisely, they must either be definition_prefix itself, or begin with definition_prefix
        followed by a '-' character)
        """
        return ''

    def js_declaration(self):
        """
        Returns a Javascript expression string, or None if this block does not require any
        Javascript behaviour. This expression evaluates to an initializer function, a function that
        takes two arguments:
        1) the value returned by js_declaration_param, identifying relevant
        characteristics of the block content,
        2) the ID prefix
        - and applies JS behaviour to the block instance with that value and prefix.

        The parent block of this block (or the top-level page code) must ensure that this
        expression is not evaluated more than once. (The resulting initializer function can and will be
        called as many times as there are instances of this block, though.)
        """
        return None

    def js_declaration_param(self, value):
        """
        Return a Javascript expression that evaluates to a value to be passed as the 
        for the parameters that should be passed to the meta-initializer function for a block
        whose content is 'value'.

        The parent block of this block (or the top-level page code) should avoid evaluating this
        expression more times than necessary. (Roughly speaking, this means once per block instance
        for values that originate from page content, and once per block definition for values that
        are defined in the block definition, e.g. default values.)
        """
        return 'null'

    def render(self, value, prefix=''):
        """
        Render the HTML for this block with 'value' as its content.
        """
        raise NotImplemented

    def bind(self, value, prefix):
        """
        Return a BoundBlock which represents the association of this block definition with a value
        and a prefix.
        BoundBlock primarily exists as a convenience to allow rendering within templates:
        bound_block.render() rather than blockdef.render(value, prefix) which can't be called from
        within a template.
        """
        return BoundBlock(self, prefix, value)


class BoundBlock(object):
    def __init__(self, factory, prefix, value):
        self.factory = factory
        self.prefix = prefix
        self.value = value

    def render(self):
        return self.factory.render(self.value, self.prefix)

    def js_declaration_param(self):
        return self.factory.js_declaration_param(self.value)


# ==========
# Text input
# ==========

class TextInputFactory(BlockFactory):
    def render(self, value, prefix=''):
        if self.label:
            return format_html(
                """<label for="{prefix}">{label}</label> <input type="text" name="{prefix}" id="{prefix}" value="{value}">""",
                prefix=prefix, label=self.label, value=value
            )
        else:
            return format_html(
                """<input type="text" name="{prefix}" id="{prefix}" value="{value}">""",
                prefix=prefix, label=self.label, value=value
            )

class TextInput(BlockOptions):
    factory = TextInputFactory
    default = ''


# =======
# Chooser
# =======

class ChooserFactory(BlockFactory):
    class Media:
        js = ['js/blocks/chooser.js']

    def js_declaration(self):
        return "Chooser('%s')" % self.definition_prefix

    def render(self, value, prefix=''):
        if self.label:
            return format_html(
                """<label>{label}</label> <input type="button" id="{prefix}-button" value="Choose a thing">""",
                label=self.label, prefix=prefix
            )
        else:
            return format_html(
                """<input type="button" id="{prefix}-button" value="Choose a thing">""",
                prefix=prefix
            )

class Chooser(BlockOptions):
    factory = ChooserFactory
    default = None


# ===========
# StructBlock
# ===========

class StructFactory(BlockFactory):
    def __init__(self, *args, **kwargs):
        super(StructFactory, self).__init__(*args, **kwargs)

        self.child_factories = []
        self.child_factories_by_name = {}
        for (name, opts) in self.block_options.child_definitions:
            prefix = "%s-%s" % (self.definition_prefix, name)
            factory = opts.factory(opts, name=name, definition_prefix=prefix)
            self.child_factories.append(factory)
            self.child_factories_by_name[name] = factory

        self.child_js_declarations_by_name = {}
        for factory in self.child_factories:
            js_declaration = factory.js_declaration()
            if js_declaration is not None:
                self.child_js_declarations_by_name[factory.name] = js_declaration

    def html_declarations(self):
        return format_html_join('\n', '{0}', [
            (child_factory.html_declarations(),)
            for child_factory in self.child_factories
        ])

    def js_declaration(self):
        # skip JS setup entirely if no children have js_declarations
        if not self.child_js_declarations_by_name:
            return None

        return "StructBlock(%s)" % js_dict(self.child_js_declarations_by_name)

    def js_declaration_param(self, value):
        # Return value should be a mapping:
        # {
        #    'firstChild': js_declaration_param_for_first_child,
        #    'secondChild': js_declaration_param_for_second_child
        # }
        # - for each child that provides a js_declaration.

        child_params = {}

        for child_name in self.child_js_declarations_by_name.keys():
            factory = self.child_factories_by_name[child_name]
            child_value = value.get(child_name, factory.default)
            child_params[child_name] = factory.js_declaration_param(child_value)

        return js_dict(child_params)

    @property
    def media(self):
        media = Media(js=['js/blocks/struct.js'])
        for item in self.child_factories:
            media += item.media
        return media

    def render(self, value, prefix=''):
        child_renderings = [
            factory.render(
                value.get(factory.name, factory.default), prefix="%s-%s" % (prefix, factory.name)
            )
            for factory in self.child_factories
        ]

        list_items = format_html_join('\n', "<li>{0}</li>", [
            [child_rendering]
            for child_rendering in child_renderings
        ])

        if self.label:
            return format_html("<label>{0}</label> <ul>{1}</ul>", self.label, list_items)
        else:
            return format_html("<ul>{0}</ul>", list_items)

class StructBlock(BlockOptions):
    def __init__(self, child_definitions, **kwargs):
        super(StructBlock, self).__init__(**kwargs)
        self.child_definitions = child_definitions

    factory = StructFactory
    default = {}


# =========
# ListBlock
# =========

class ListFactory(BlockFactory):
    def __init__(self, *args, **kwargs):
        super(ListFactory, self).__init__(*args, **kwargs)

        child_block_options = self.block_options.child_block_options
        self.child_factory = child_block_options.factory(child_block_options,
            definition_prefix=self.definition_prefix + '-child')
        self.template_child = self.child_factory.bind(self.child_factory.default, '__PREFIX__')
        self.child_js_declaration = self.child_factory.js_declaration()

    @property
    def media(self):
        return Media(js=['js/blocks/macro.js', 'js/blocks/list.js']) + self.child_factory.media

    def html_declarations(self):
        template_declaration = format_html(
            '<script type="text/template" id="{0}-template">{1}</script>',
            self.definition_prefix, self.template_child.render()
        )
        child_declarations = self.child_factory.html_declarations()
        return mark_safe(template_declaration + child_declarations)

    def js_declaration(self):
        opts = {'definitionPrefix': "'%s'" % self.definition_prefix}

        if self.child_js_declaration:
            opts['childInitializer'] = self.child_js_declaration
            opts['templateChildParam'] = self.template_child.js_declaration_param()

        return "ListBlock(%s)" % js_dict(opts)

    def js_declaration_param(self, value):
        if self.child_js_declaration:
            # Return value is an array of js_declaration_params, one for each child block in the list
            child_params = [
                indent(self.child_factory.js_declaration_param(child_value))
                for child_value in value
            ]
            return '[\n%s\n]' % ',\n'.join(child_params)
        else:
            return '[]'

    def render(self, value, prefix=''):
        return render_to_string('core/blocks/list.html', {
            'label': self.label,
            'prefix': prefix,
            'children': [
                self.child_factory.bind(child_val, prefix="%s-%d" % (prefix, i))
                for (i, child_val) in enumerate(value)
            ],
        })

class ListBlock(BlockOptions):
    def __init__(self, child_block_options, **kwargs):
        super(ListBlock, self).__init__(**kwargs)
        self.child_block_options = child_block_options

    factory = ListFactory
    default = []


# class StreamBlock(Block):
#     def __init__(self, child_defs, **kwargs):
#         self.child_defs = child_defs
#         self.default = kwargs.get('default', [])
#         self.label = kwargs.get('label', '')

#         self.child_defs_by_name = {}
#         self.template_children = {}
#         for name, child_def in self.child_defs:
#             self.child_defs_by_name[name] = child_def
#             self.template_children[name] = child_def(prefix="__PREFIX__")

#     def html_declarations(self, definition_prefix):
#         child_def_declarations = [
#             format_html(
#                 """
#                     {html_declarations}
#                     <script type="text/template" id="{definition_prefix}-template-{child_name}">
#                         {child_template}
#                     </script>
#                 """,
#                 html_declarations=child_def.html_declarations("%s-child-%s" % (definition_prefix, name)),
#                 definition_prefix=definition_prefix,
#                 child_name=name,
#                 child_template=self.template_children[name].render()
#             )
#             for (name, child_def) in self.child_defs
#         ]
#         menu_html = render_to_string('core/blocks/stream_menu.html', {
#             'child_names': [name for (name, child_def) in self.child_defs],
#             'prefix': '__PREFIX__'
#         })
#         menu_declaration = format_html(
#             """<script type="text/template" id="{definition_prefix}-menutemplate">{menu_html}</script>""",
#             definition_prefix=definition_prefix, menu_html=menu_html)

#         return mark_safe('\n'.join(child_def_declarations) + menu_declaration)

#     def js_initializer(self, definition_prefix):
#         child_js_defs = [
#             """{{
#                 'name': '{child_name}',
#                 'initializer': {initializer}
#             }}""".format(
#                 child_name=name,
#                 initializer=child_def.js_initializer("%s-child-%s" % (definition_prefix, name)) or 'null'
#             )
#             for name, child_def in self.child_defs
#         ]

#         return "StreamBlock([\n%s\n])" % ',\n'.join(child_js_defs)

#     @property
#     def media(self):
#         media = Media(js=['js/blocks/stream.js'])
#         for name, item in self.child_defs:
#             media += item.media
#         return media

#     def render(self, value, prefix=''):
#         child_records = []
#         index = 0

#         for item in value:
#             child_def = self.child_defs_by_name.get(item['type'])
#             if child_def:
#                 child = child_def(item['value'], prefix="%s-%d-item" % (prefix, index))
#                 child_records.append((index, item['type'], child))
#                 index += 1

#         return render_to_string('core/blocks/stream.html', {
#             'label': self.label,
#             'prefix': prefix,
#             'child_records': child_records,
#             'child_type_names': [name for (name, child_def) in self.child_defs],
#         })
