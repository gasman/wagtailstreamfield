from django.shortcuts import render

from core.blocks import TextInput, Chooser, StructBlock, ListBlock

def home(request):
    SpeakerBlock = StructBlock([
        ('name', TextInput(label='Name')),
        ('job_title', TextInput(label='Job title', default="just this guy, y'know?")),
        ('nicknames', ListBlock(TextInput(label='Nickname'), label='Nicknames')),
        ('image', Chooser(label='Image')),
    ])
    page_def = StructBlock([
        ('title', TextInput(label='Title')),
        ('speakers', ListBlock(SpeakerBlock, label='Speakers')),
    ])

    page = page_def({
        'title': 'My lovely event',
        'speakers': [
            {'name': 'Tim Berners-Lee', 'job_title': 'Web developer', 'nicknames': ['Timmy', 'Bernie']},
            {'name': 'Bono', 'job_title': 'Singer'},
        ]
    }, prefix='page')

    return render(request, 'core/home.html', {
        'media': page_def.media,
        'declarations': page_def.html_declarations('blockdef-page'),
        'constructor': page_def.js_constructor('blockdef-page'),
        'page': page,
    })
