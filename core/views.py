from django.shortcuts import render

from core.blocks import TextInput, Chooser, StructBlock#, ListBlock, StreamBlock

def home(request):
    SpeakerBlock = StructBlock([
        ('name', TextInput(label='Name')),
        ('job_title', TextInput(label='Job title', default="just this guy, y'know?")),
        #('nicknames', ListBlock(TextInput(label='Nickname'), label='Nicknames')),
        ('image', Chooser(label='Image')),
    ])

    page_def = StructBlock([
        ('title', TextInput(label='Title')),
        ('speaker', SpeakerBlock),
#        ('speakers', ListBlock(SpeakerBlock, label='Speakers')),
#        ('content', StreamBlock([
#            ('heading', TextInput(label='Heading')),
#            ('image', Chooser(label='Image'))
#        ])),
    ])

    page_data = {
        'title': 'My lovely event',
        'speaker': {'name': 'Tim Berners-Lee', 'job_title': 'Web developer', 'nicknames': ['Timmy', 'Bernie']},
    }

    # page = page_def({
    #     'title': 'My lovely event',
    #     'speakers': [
    #         {'name': 'Tim Berners-Lee', 'job_title': 'Web developer', 'nicknames': ['Timmy', 'Bernie']},
    #         {'name': 'Bono', 'job_title': 'Singer'},
    #     ],
    #     'content': [
    #         {'type': 'heading', 'value': "The largest event for the things that the event is about!"},
    #         {'type': 'image', 'value': 42},
    #         {'type': 'heading', 'value': "Earlyish Bird tickets available now"},
    #         {'type': 'image', 'value': 99},
    #     ],
    # }, prefix='page')

    page_def = SpeakerBlock
    page_data = {'name': 'Tim Berners-Lee', 'job_title': 'Web developer'}

    page_factory = page_def.factory(page_def, definition_prefix='def')
    page = page_factory.bind(page_data, prefix='page')

    return render(request, 'core/home.html', {
        'media': page_factory.media,
        'declarations': page_factory.html_declarations(),
        'initializer': page_factory.js_declaration(),
        'page': page,
    })
