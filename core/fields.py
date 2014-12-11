from django import forms
from django.utils.html import format_html

from collections import OrderedDict

class StructWidget(forms.Widget):
    def __init__(self, form_class, **kwargs):
        super(StructWidget, self).__init__(**kwargs)
        self.form_class = form_class

    def render(self, name, value, attrs=None):
        form = self.form_class(initial=value, prefix=name)
        return format_html('<ul>{0}</ul>', form.as_ul())

    # def id_for_label(self, id_):
    #     try:
    #         (name, field) = self.form_class.base_fields.items()[0]
    #     except IndexError:
    #         return None

    #     return field.widget.id_for_label("%s-%s" % (id_, name))

class StructField(forms.Field):
    def __init__(self, fields, **kwargs):
        # Create a subclass of BaseForm with a base_fields list formed of the passed fields
        form_class = type('StructFieldForm', (forms.BaseForm,), {'base_fields': OrderedDict(fields)})

        if 'widget' not in kwargs:
            kwargs['widget'] = StructWidget(form_class)
        super(StructField, self).__init__(**kwargs)
