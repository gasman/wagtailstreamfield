import re
import copy
from collections import OrderedDict

from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.template.loader import render_to_string
from django.forms import Media

import six

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
        pass

class BlockFactory(object):
    creation_counter = 0

    """
    Setting a 'dependencies' list serves as a shortcut for the common case where a complex block type
    (such as struct, list or stream) relies on one or more inner factory objects, and needs to ensure that
    the responses from the 'media' and 'html_declarations' include the relevant declarations for those inner
    factories, as well as its own. Specifying these inner factory objects in a 'dependencies' list means that
    the base 'media' and 'html_declarations' methods will return those declarations; the outer block type can
    then add its own declarations to the list by overriding those methods and using super().
    """
    dependencies = set()

    def all_blocks(self):
        """
        Return a set consisting of self and all block objects that are direct or indirect dependencies
        of this block
        """
        result = set([self])
        for dep in self.dependencies:
            result |= dep.all_blocks()
        return result

    def all_media(self):
        media = Media()
        for block in self.all_blocks():
            media += block.media
        return media

    def all_html_declarations(self):
        declarations = filter(bool, [block.html_declarations() for block in self.all_blocks()])
        return mark_safe('\n'.join(declarations))

    def __init__(self, **kwargs):
        if 'default' in kwargs:
            self.default = kwargs['default']  # if not specified, leave as the class-level default
        self.label = kwargs.get('label', None)

        # Increase the creation counter, and save our local copy.
        self.creation_counter = BlockFactory.creation_counter
        BlockFactory.creation_counter += 1
        self.definition_prefix = 'blockdef-%d' % self.creation_counter

    def set_name(self, name):
        self.name = name

        # if we don't have a label already, generate one from name
        if self.label is None:
            self.label = capfirst(name.replace('_', ' '))

    @property
    def media(self):
        return Media()

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
        raise NotImplementedError('%s.render' % self.__class__)

    def value_from_datadict(self, data, files, prefix):
        raise NotImplementedError('%s.value_from_datadict' % self.__class__)

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
    default = ''

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

    def value_from_datadict(self, data, files, prefix):
        return data.get(prefix, '')


# ===========
# Field block
# ===========

class FieldFactory(BlockFactory):
    default = None

    def __init__(self, field, **kwargs):
        super(FieldFactory, self).__init__(**kwargs)
        self.field = field

    def render(self, value, prefix=''):
        widget = self.field.widget

        widget_html = widget.render(prefix, value, {'id': prefix})
        if self.label:
            return format_html(
                """<label for={label_id}>{label}</label> {widget_html}""",
                label_id=widget.id_for_label(prefix), label=self.label, widget_html=widget_html
            )
        else:
            return widget_html

    def value_from_datadict(self, data, files, prefix):
        return self.field.widget.value_from_datadict(data, files, prefix)

# =======
# Chooser
# =======

class ChooserFactory(BlockFactory):
    default = None

    @property
    def media(self):
        return Media(js=['js/blocks/chooser.js'])

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

    def value_from_datadict(self, data, files, prefix):
        return 123


# ===========
# StructBlock
# ===========

class BaseStructFactory(BlockFactory):
    default = {}

    def __init__(self, local_blocks=None, **kwargs):
        super(BaseStructFactory, self).__init__(**kwargs)

        self.child_factories = copy.deepcopy(self.base_blocks)
        if local_blocks:
            for name, factory in local_blocks:
                factory.set_name(name)
                self.child_factories[name] = factory

        self.child_js_initializers = {}
        for name, factory in self.child_factories.items():
            js_initializer = factory.js_initializer()
            if js_initializer is not None:
                self.child_js_initializers[name] = js_initializer

        self.dependencies = set(self.child_factories.values())

    def js_initializer(self):
        # skip JS setup entirely if no children have js_initializers
        if not self.child_js_initializers:
            return None

        return "StructBlock(%s)" % js_dict(self.child_js_initializers)

    def js_initializer_param(self, value):
        # Return value should be a mapping:
        # {
        #    'firstChild': js_initializer_param_for_first_child,
        #    'secondChild': js_initializer_param_for_second_child
        # }
        # - for each child that provides a js_initializer.

        child_params = {}

        for child_name in self.child_js_initializers.keys():
            factory = self.child_factories[child_name]
            child_value = value.get(child_name, factory.default)
            child_params[child_name] = factory.js_initializer_param(child_value)

        return js_dict(child_params)

    @property
    def media(self):
        return Media(js=['js/blocks/struct.js'])

    def render(self, value, prefix=''):
        child_renderings = [
            factory.render(
                value.get(name, factory.default), prefix="%s-%s" % (prefix, name)
            )
            for name, factory in self.child_factories.items()
        ]

        list_items = format_html_join('\n', "<li>{0}</li>", [
            [child_rendering]
            for child_rendering in child_renderings
        ])

        if self.label:
            return format_html("<label>{0}</label> <ul>{1}</ul>", self.label, list_items)
        else:
            return format_html("<ul>{0}</ul>", list_items)

    def value_from_datadict(self, data, files, prefix):
        return dict([
            (name, factory.value_from_datadict(data, files, '%s-%s' % (prefix, name)))
            for name, factory in self.child_factories.items()
        ])

class DeclarativeSubBlocksMetaclass(type):
    """
    Metaclass that collects sub-blocks declared on the base classes.
    (cheerfully stolen from https://github.com/django/django/blob/master/django/forms/forms.py)
    """
    def __new__(mcs, name, bases, attrs):
        # Collect sub-blocks from current class.
        current_blocks = []
        for key, value in list(attrs.items()):
            if isinstance(value, BlockFactory):
                current_blocks.append((key, value))
                value.set_name(key)
                attrs.pop(key)
        current_blocks.sort(key=lambda x: x[1].creation_counter)
        attrs['declared_blocks'] = OrderedDict(current_blocks)

        new_class = (super(DeclarativeSubBlocksMetaclass, mcs)
            .__new__(mcs, name, bases, attrs))

        # Walk through the MRO.
        declared_blocks = OrderedDict()
        for base in reversed(new_class.__mro__):
            # Collect sub-blocks from base class.
            if hasattr(base, 'declared_blocks'):
                declared_blocks.update(base.declared_blocks)

            # Field shadowing.
            for attr, value in base.__dict__.items():
                if value is None and attr in declared_blocks:
                    declared_blocks.pop(attr)

        new_class.base_blocks = declared_blocks
        new_class.declared_blocks = declared_blocks

        return new_class

class StructFactory(six.with_metaclass(DeclarativeSubBlocksMetaclass, BaseStructFactory)):
    pass

class InheritableBlockOptions(BlockOptions):
    """A special case of BlockOptions as used by StreamBlock where child_definitions
    can be defined either by subclassing or by being passed to __init__"""
    def __init__(self, child_factories=None, **kwargs):
        # look in our own __dict__ for child BlockFactories that have been added by subclassing
        self.child_factories = [
            item for item in self.__class__.__dict__.items() if isinstance(item[1], BlockFactory)
        ]
        # FIXME: looping over __dict__ like this won't pick up fields defined on a superclass
        # (e.g. StructBlock -> SpeakerBlock -> ExpertSpeakerBlock)
        self.child_factories.sort(key=lambda x: x[1].creation_counter)

        super(InheritableBlockOptions, self).__init__(**kwargs)

        if child_factories:
            self.child_factories += [
                # convert child definitions to instances if they've been passed as classes
                (name, factory() if isinstance(factory, type) else factory)
                for (name, factory) in child_factories
            ]


# =========
# ListBlock
# =========

class ListFactory(BlockFactory):
    default = []

    def __init__(self, child_factory, **kwargs):
        super(ListFactory, self).__init__(**kwargs)

        if isinstance(child_factory, type):
            # child_factory was passed as a class, so convert it to a factory instance
            self.child_factory = child_factory()
        else:
            self.child_factory = child_factory

        self.dependencies = set([self.child_factory])
        self.child_js_initializer = self.child_factory.js_initializer()

    @property
    def media(self):
        return Media(js=['js/blocks/sequence.js', 'js/blocks/list.js'])

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

        return format_html(
            '<script type="text/template" id="{0}-newmember">{1}</script>',
            self.definition_prefix, list_member_html
        )

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

    def value_from_datadict(self, data, files, prefix):
        count = int(data['%s-count' % prefix])
        values_with_indexes = []
        for i in range(0, count):
            if data['%s-%d-deleted' % (prefix, i)]:
                pass
            values_with_indexes.append(
                (
                    data['%s-%d-order' % (prefix, i)],
                    self.child_factory.value_from_datadict(data, files, '%s-%d-value' % (prefix, i))
                )
            )

        values_with_indexes.sort()
        return [v for (i, v) in values_with_indexes]


# ===========
# StreamBlock
# ===========

class StreamFactory(BlockFactory):
    default = []

    def __init__(self, block_options, **kwargs):
        super(StreamFactory, self).__init__(**kwargs)

        self.child_factories = OrderedDict()
        for name, factory in block_options.child_factories.items():
            factory.set_name(name)
            self.child_factories[name] = factory

        self.dependencies = set(self.child_factories.values())

    def render_list_member(self, block_type_name, value, prefix, index):
        """
        Render the HTML for a single list item. This consists of an <li> wrapper, hidden fields
        to manage ID/deleted state/type, delete/reorder buttons, and the child block's own HTML.
        """
        child_factory = self.child_factories[block_type_name]
        child = child_factory.bind(value, prefix="%s-value" % prefix)
        return render_to_string('core/blocks/stream_member.html', {
            'child_factories': self.child_factories.values(),
            'block_type_name': block_type_name,
            'prefix': prefix,
            'child': child,
            'index': index,
        })

    def html_declarations(self):
        return format_html_join(
            '\n', '<script type="text/template" id="{0}-newmember-{1}">{2}</script>',
            [
                (
                    self.definition_prefix,
                    name,
                    self.render_list_member(name, child_factory.default, '__PREFIX__', '')
                )
                for name, child_factory in self.child_factories.items()
            ]
        )

    @property
    def media(self):
        return Media(js=['js/blocks/sequence.js', 'js/blocks/stream.js'])

    def js_initializer(self):
        # compile a list of info dictionaries, one for each available block type
        child_blocks = []
        for name, child_factory in self.child_factories.items():
            # each info dictionary specifies at least a block name
            child_block_info = {'name': "'%s'" % name}

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
            indent(self.child_factories[child['type']].js_initializer_param(child['value']))
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
            'child_factories': self.child_factories.values(),
            'header_menu_prefix': '%s-before' % prefix,
        })

    def value_from_datadict(self, data, files, prefix):
        count = int(data['%s-count' % prefix])
        values_with_indexes = []
        for i in range(0, count):
            if data['%s-%d-deleted' % (prefix, i)]:
                pass
            block_type_name = data['%s-%d-type' % (prefix, i)]
            child_factory = self.child_factories[block_type_name]

            values_with_indexes.append(
                (
                    data['%s-%d-order' % (prefix, i)],
                    block_type_name,
                    child_factory.value_from_datadict(data, files, '%s-%d-value' % (prefix, i))
                )
            )

        values_with_indexes.sort()
        return [{'type': t, 'value': v} for (i, t, v) in values_with_indexes]

class StreamBlock(InheritableBlockOptions):
    class Meta:
        factory = StreamFactory
