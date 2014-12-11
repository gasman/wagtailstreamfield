from django.shortcuts import render
from django import forms
from django.http import HttpResponse

from core.blocks import TextInput, Chooser, StructBlock, ListBlock, StreamBlock, FieldBlock
from core.fields import StructField

class SpeakerBlock(StructBlock):
    name = FieldBlock(StructField([
        ('first_name', forms.CharField()),
        ('surname', forms.CharField()),
    ]))
    job_title = TextInput(default="just this guy, y'know?")
    nicknames = ListBlock(TextInput)
    image = Chooser()

class ContentBlock(StreamBlock):
    heading = TextInput()
    image = Chooser(label='Image')

#class ExpertSpeakerBlock(SpeakerBlock):
#    specialist_subject = TextInput()

def home(request):
    page_def = StructBlock([
        ('title', FieldBlock(forms.CharField(), label='Title')),
        ('speakers', ListBlock(SpeakerBlock(), label='Speakers')),
        ('content', ContentBlock([
            ('speaker', SpeakerBlock([('another_specialist_subject', TextInput)], label='Featured speaker')),
        ])),
    ])

    page_data = {
        'title': 'My lovely event',
        'speakers': [
            {'name': {'first_name': 'Tim', 'surname': 'Berners-Lee'}, 'job_title': 'Web developer', 'nicknames': ['Timmy', 'Bernie']},
            {'name': {'first_name': 'Bono', 'surname': 'Farquharson'}, 'job_title': 'Singer'},
        ],
        'content': [
            {'type': 'heading', 'value': "The largest event for the things that the event is about!"},
            {'type': 'image', 'value': 42},
            {'type': 'heading', 'value': "Earlyish Bird tickets available now"},
            {'type': 'image', 'value': 99},
        ],
    }

    page_factory = page_def.Meta.factory(page_def, definition_prefix='def')
    page = page_factory.bind(page_data, prefix='page')

    return render(request, 'core/home.html', {
        'media': page_factory.media,
        'declarations': page_factory.html_declarations(),
        'initializer': page_factory.js_initializer(),
        'page': page,
    })


class PersonForm(forms.Form):
    name = StructField([
        ('first_name', forms.CharField()),
        ('surname', forms.CharField()),
    ])
    job_title = forms.CharField()

def formtest(request):
    if request.method == 'POST':
        form = PersonForm(request.POST)
        if form.is_valid():
            return HttpResponse(repr(form.cleaned_data), mimetype='text/plain')
    else:
        form = PersonForm()

    return render(request, 'core/formtest.html', {
        'form': form
    })
