from django.shortcuts import render
from django import forms
from django.http import HttpResponse
from django.core.exceptions import ValidationError

from core.blocks import TextInputBlock, ChooserBlock, StructBlock, ListBlock, StreamBlock, FieldBlock

class SpeakerBlock(StructBlock):
    name = FieldBlock(forms.CharField(), label='Full name')
    job_title = TextInputBlock(default="just this guy, y'know?")
    nicknames = ListBlock(TextInputBlock())
    image = ChooserBlock()

class ContentBlock(StreamBlock):
    heading = TextInputBlock()
    image = ChooserBlock(label='Image')

class ExpertSpeakerBlock(SpeakerBlock):
    image = None
    specialist_subject = TextInputBlock()

PAGE_DEF = StructBlock([
    ('title', FieldBlock(forms.CharField(), label='Title')),
    ('speakers', ListBlock(SpeakerBlock(), label='Speakers')),
    ('content', ContentBlock([
        ('speaker', ExpertSpeakerBlock([('another_specialist_subject', TextInputBlock())], label='Featured speaker')),
    ])),
])

PAGE_DATA = {
    'title': 'My lovely event',
    'speakers': [
        {'name': 'Tim Berners-Lee', 'job_title': 'Web developer', 'nicknames': ['Timmy', 'Bernie']},
        {'name': 'Bono', 'job_title': 'Singer'},
    ],
    'content': [
        {'type': 'heading', 'value': "The largest event for the things that the event is about!"},
        {'type': 'image', 'value': 42},
        {'type': 'heading', 'value': "Earlyish Bird tickets available now"},
        {'type': 'image', 'value': 99},
    ],
}

def edit(request):
    if request.method == 'POST':
        value = PAGE_DEF.value_from_datadict(request.POST, request.FILES, 'page')
        try:
            clean_value = PAGE_DEF.clean(value)
        except ValidationError as e:
            page = PAGE_DEF.bind(value, prefix='page', error=e)

            return render(request, 'core/home.html', {
                'media': PAGE_DEF.all_media(),
                'html_declarations': PAGE_DEF.all_html_declarations(),
                'initializer': PAGE_DEF.js_initializer(),
                'page': page,
            })
        else:
            return HttpResponse(repr(clean_value), content_type="text/plain")
    else:

        page = PAGE_DEF.bind(PAGE_DATA, prefix='page')

        return render(request, 'core/edit.html', {
            'media': PAGE_DEF.all_media(),
            'html_declarations': PAGE_DEF.all_html_declarations(),
            'initializer': PAGE_DEF.js_initializer(),
            'page': page,
        })
