from django.shortcuts import render
from django import forms
from django.http import HttpResponse

from core.blocks import TextInputBlock, ChooserBlock, StructBlock, ListBlock, StreamBlock, FieldBlock

class SpeakerBlock(StructBlock):
    name = TextInputBlock(label='Full name')
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

def home(request):
    page_data = {
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

    if request.method == 'POST':
        return HttpResponse(
            repr(PAGE_DEF.value_from_datadict(request.POST, request.FILES, 'page')), mimetype="text/plain")
    else:

        page = PAGE_DEF.bind(page_data, prefix='page')

        return render(request, 'core/home.html', {
            'media': PAGE_DEF.all_media(),
            'html_declarations': PAGE_DEF.all_html_declarations(),
            'initializer': PAGE_DEF.js_initializer(),
            'page': page,
        })
