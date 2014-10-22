from django.shortcuts import render

from core.blocks import TextInput, Chooser, StructBlock, ListBlock, StreamBlock

def home(request):
    # TODO: ensure that declarations get output the right number of times when SpeakerBlock is
    # referenced multiple times on a page
    SpeakerBlock = StructBlock([
        ('name', TextInput(label='Name')),
        ('job_title', TextInput(label='Job title', default="just this guy, y'know?")),
        ('nicknames', ListBlock(TextInput(label='Nickname'), label='Nicknames')),
        ('image', Chooser(label='Image')),
    ])

    page_def = StructBlock([
        ('title', TextInput(label='Title')),
        ('speakers', ListBlock(SpeakerBlock, label='Speakers')),
        ('content', StreamBlock([
            ('heading', TextInput(label='Heading')),
            ('image', Chooser(label='Image'))
        ])),
    ])

    page = page_def({
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
    }, prefix='page')

    return render(request, 'core/home.html', {
        'media': page_def.media,
        'declarations': page_def.html_declarations('blockdef-page'),
        'initializer': page_def.js_initializer('blockdef-page'),
        'page': page,
    })
