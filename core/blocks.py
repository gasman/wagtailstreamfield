import re

from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.template.loader import render_to_string
from django.forms import Media

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

class BlockFactory(object):
    """
    Setting a 'dependencies' list serves as a shortcut for the common case where a complex block type
    (such as struct, list or stream) relies on one or more inner factory objects, and needs to ensure that
    the responses from the 'media' and 'html_declarations' include the relevant declarations for those inner
    factories, as well as its own. Specifying these inner factory objects in a 'dependencies' list means that
    the base 'media' and 'html_declarations' methods will return those declarations; the outer block type can
    then add its own declarations to the list by overriding those methods and using super().
    """
    dependencies = []

    def __init__(self, block_options, name=None, definition_prefix=''):
        self.block_options = block_options
        self.name = name
        self.definition_prefix = definition_prefix

        self.default = self.block_options.default

        # Try to get a field label from block_options, or failing that, generate one from name
        self.label = getattr(block_options, 'label', None)
        if self.label is None and self.name is not None:
            self.label = capfirst(self.name.replace('_', ' '))

    @property
    def media(self):
        media = Media()
        for dep in self.dependencies:
            media += dep.media
        return media

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
        return format_html_join('\n', '{0}', [
            (dep.html_declarations(),)
            for dep in self.dependencies
        ])

    def js_initializer(self):
        """
        Returns a Javascript expression string, or None if this block does not require any
        Javascript behaviour. This expression evaluates to an initializer function, a function that
        takes two arguments:
        1) the value returned by js_initializer_param, identifying relevant
        characteristics of the block content,
        2) the ID prefix
        - and applies JS behaviour to the block instance with that value and prefix.

        The parent block of this block (or the top-level page code) must ensure that this
        expression is not evaluated more than once. (The resulting initializer function can and will be
        called as many times as there are instances of this block, though.)
        """
        return None

    def js_initializer_param(self, value):
        """
        Given a block value, return a Javascript expression string that incorporates all information
        about that value that the initializer function needs to know.

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

    def prototype_block(self):
        """
        Return a BoundBlock that can be used as a basis for new empty block instances to be added on the fly
        (new list items, for example). This will have a prefix of '__PREFIX__' (to be dynamically replaced with
        a real prefix when it's inserted into the page) and a value equal to the block factory's default value.
        """
        return self.bind(self.default, '__PREFIX__')


class BoundBlock(object):
    def __init__(self, factory, prefix, value):
        self.factory = factory
        self.prefix = prefix
        self.value = value

    def render(self):
        return self.factory.render(self.value, self.prefix)

    def js_initializer_param(self):
        return self.factory.js_initializer_param(self.value)


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
    @property
    def media(self):
        return super(ChooserFactory, self).media + Media(js=['js/blocks/chooser.js'])

    def js_initializer(self):
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

        self.child_js_initializers_by_name = {}
        for factory in self.child_factories:
            js_initializer = factory.js_initializer()
            if js_initializer is not None:
                self.child_js_initializers_by_name[factory.name] = js_initializer

        self.dependencies = self.child_factories

    def js_initializer(self):
        # skip JS setup entirely if no children have js_initializers
        if not self.child_js_initializers_by_name:
            return None

        return "StructBlock(%s)" % js_dict(self.child_js_initializers_by_name)

    def js_initializer_param(self, value):
        # Return value should be a mapping:
        # {
        #    'firstChild': js_initializer_param_for_first_child,
        #    'secondChild': js_initializer_param_for_second_child
        # }
        # - for each child that provides a js_initializer.

        child_params = {}

        for child_name in self.child_js_initializers_by_name.keys():
            factory = self.child_factories_by_name[child_name]
            child_value = value.get(child_name, factory.default)
            child_params[child_name] = factory.js_initializer_param(child_value)

        return js_dict(child_params)

    @property
    def media(self):
        return super(StructFactory, self).media + Media(js=['js/blocks/struct.js'])

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
        self.child_js_initializer = self.child_factory.js_initializer()
        self.dependencies = [self.child_factory]

    @property
    def media(self):
        return super(ListFactory, self).media + Media(js=['js/blocks/sequence.js', 'js/blocks/list.js'])

    def render_list_member(self, value, prefix, index):
        """
        Render the HTML for a single list item. This consists of an <li> wrapper, hidden fields
        to manage ID/deleted state, delete/reorder buttons, and the child block's own HTML.
        """
        child = self.child_factory.bind(value, prefix="%s-value" % prefix)
        return render_to_string('core/blocks/list_member.html', {
            'prefix': prefix,
            'child': child,
            'index': index,
        })

    def html_declarations(self):
        # generate the HTML to be used when adding a new item to the list;
        # this is the output of render_list_member as rendered with the prefix '__PREFIX__'
        # (to be replaced dynamically when adding the new item) and the child block's default value
        # as its value.
        list_member_html = self.render_list_member(self.child_factory.default, '__PREFIX__', '')

        template_declaration = format_html(
            '<script type="text/template" id="{0}-newmember">{1}</script>',
            self.definition_prefix, list_member_html
        )
        return mark_safe(super(ListFactory, self).html_declarations() + template_declaration)

    def js_initializer(self):
        opts = {'definitionPrefix': "'%s'" % self.definition_prefix}

        if self.child_js_initializer:
            opts['childInitializer'] = self.child_js_initializer
            opts['templateChildParam'] = self.child_factory.prototype_block().js_initializer_param()

        return "ListBlock(%s)" % js_dict(opts)

    def js_initializer_param(self, value):
        if self.child_js_initializer:
            # Return value is an array of js_initializer_params, one for each child block in the list
            child_params = [
                indent(self.child_factory.js_initializer_param(child_value))
                for child_value in value
            ]
            return '[\n%s\n]' % ',\n'.join(child_params)
        else:
            return '[]'

    def render(self, value, prefix=''):
        list_members_html = [
            self.render_list_member(child_val, "%s-%d" % (prefix, i), i)
            for (i, child_val) in enumerate(value)
        ]

        return render_to_string('core/blocks/list.html', {
            'label': self.label,
            'prefix': prefix,
            'list_members_html': list_members_html,
        })

class ListBlock(BlockOptions):
    def __init__(self, child_block_options, **kwargs):
        super(ListBlock, self).__init__(**kwargs)
        self.child_block_options = child_block_options

    factory = ListFactory
    default = []


# ===========
# StreamBlock
# ===========

class StreamFactory(BlockFactory):
    def __init__(self, *args, **kwargs):
        super(StreamFactory, self).__init__(*args, **kwargs)

        self.child_factories = []
        self.child_factories_by_name = {}

        for (name, opts) in self.block_options.child_definitions:
            prefix = "%s-child-%s" % (self.definition_prefix, name)
            factory = opts.factory(opts, name=name, definition_prefix=prefix)
            self.child_factories.append(factory)
            self.child_factories_by_name[name] = factory

        self.dependencies = self.child_factories

    def render_list_member(self, block_type_name, value, prefix, index):
        """
        Render the HTML for a single list item. This consists of an <li> wrapper, hidden fields
        to manage ID/deleted state/type, delete/reorder buttons, and the child block's own HTML.
        """
        child_factory = self.child_factories_by_name[block_type_name]
        child = child_factory.bind(value, prefix="%s-value" % prefix)
        return render_to_string('core/blocks/stream_member.html', {
            'child_factories': self.child_factories,
            'block_type_name': block_type_name,
            'prefix': prefix,
            'child': child,
            'index': index,
        })

    def html_declarations(self):
        template_declarations = format_html_join(
            '\n', '<script type="text/template" id="{0}-newmember-{1}">{2}</script>',
            [
                (
                    self.definition_prefix,
                    child_factory.name,
                    self.render_list_member(child_factory.name, child_factory.default, '__PREFIX__', '')
                )
                for child_factory in self.child_factories
            ]
        )
        return mark_safe(super(StreamFactory, self).html_declarations() + template_declarations)

    @property
    def media(self):
        return super(StreamFactory, self).media + Media(js=['js/blocks/sequence.js', 'js/blocks/stream.js'])

    def js_initializer(self):
        # compile a list of info dictionaries, one for each available block type
        child_blocks = []
        for child_factory in self.child_factories:
            # each info dictionary specifies at least a block name
            child_block_info = {'name': "'%s'" % child_factory.name}

            # if the child defines a JS initializer function, include that in the info dict
            # along with the param that needs to be passed to it for initializing an empty/default block
            # of that type
            child_js_initializer = child_factory.js_initializer()
            if child_js_initializer:
                child_block_info['initializer'] = child_js_initializer
                child_block_info['templateInitializerParam'] = child_factory.prototype_block().js_initializer_param()

            child_blocks.append(indent(js_dict(child_block_info)))

        opts = {
            'definitionPrefix': "'%s'" % self.definition_prefix,
            'childBlocks': '[\n%s\n]' % ',\n'.join(child_blocks),
        }

        return "StreamBlock(%s)" % js_dict(opts)

    def js_initializer_param(self, value):
        # Return value is an array of js_initializer_params, one for each child block in the list
        child_params = [
            indent(self.child_factories_by_name[child['type']].js_initializer_param(child['value']))
            for child in value
        ]
        return '[\n%s\n]' % ',\n'.join(child_params)

    def render(self, value, prefix=''):
        list_members_html = [
            self.render_list_member(member['type'], member['value'], "%s-%d" % (prefix, i), i)
            for (i, member) in enumerate(value)
        ]

        return render_to_string('core/blocks/stream.html', {
            'label': self.label,
            'prefix': prefix,
            'list_members_html': list_members_html,
            'child_factories': self.child_factories,
            'footer_menu_prefix': '%s-after' % prefix,
        })

class StreamBlock(BlockOptions):
    def __init__(self, child_definitions, **kwargs):
        super(StreamBlock, self).__init__(**kwargs)
        self.child_definitions = child_definitions

    factory = StreamFactory
    default = []
