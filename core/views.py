from django.shortcuts import render

from core.blocks import TextInput, Chooser, StructBlock, ListBlock, StreamBlock

class SpeakerBlock(StructBlock):
    name = TextInput(label='Full name')
    job_title = TextInput(default="just this guy, y'know?")
    nicknames = ListBlock(TextInput)
    image = Chooser()

def home(request):
    page_def = StructBlock([
        ('title', TextInput(label='Title')),
        ('speakers', ListBlock(SpeakerBlock(), label='Speakers')),
        ('content', StreamBlock([
            ('heading', TextInput),
            ('image', Chooser(label='Image')),
            ('speaker', SpeakerBlock([('specialist_subject', TextInput)], label='Featured speaker')),
        ])),
    ])

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

    page_factory = page_def.Meta.factory(page_def, definition_prefix='def')
    page = page_factory.bind(page_data, prefix='page')

    return render(request, 'core/home.html', {
        'media': page_factory.media,
        'declarations': page_factory.html_declarations(),
        'initializer': page_factory.js_initializer(),
        'page': page,
    })
