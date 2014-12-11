from django import forms
from django.utils.html import format_html_join

class StructWidget(forms.Widget):
    def __init__(self, widgets, **kwargs):
        super(StructWidget, self).__init__(**kwargs)
        self.widgets = widgets

    def render(self, name, value, attrs=None):
        final_attrs = self.build_attrs(attrs)

        return format_html_join('\n', '<div class="subfield">{0}</div>', [
            (
                child_widget.render(
                    '%s-%s' % (name, child_name),
                    value[child_name],
                    {'id': '%s-%s' % (final_attrs['id'], child_name)}
                ),
            )
            for (child_name, child_widget) in self.widgets
        ])

    def id_for_label(self, id_):
        try:
            (child_name, child_widget) = self.widgets[0]
        except IndexError:
            return None

        return child_widget.id_for_label("%s-%s" % (id_, child_name))

class StructField(forms.Field):
    def __init__(self, fields, **kwargs):
        if 'widget' not in kwargs:
            kwargs['widget'] = StructWidget(
                [(name, field.widget) for (name, field) in fields]
            )
        super(StructField, self).__init__(**kwargs)
