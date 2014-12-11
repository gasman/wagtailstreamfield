from django import forms

class StructField(forms.Field):
    def __init__(self, fields, **kwargs):
        super(StructField, self).__init__(**kwargs)
