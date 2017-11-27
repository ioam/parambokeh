# -*- coding: utf-8 -*-

from nbsite.shared_conf import *

project = u'ParamBokeh'
authors = u'ParamBokeh contributors'
copyright = u'2017 ' + authors
description = 'Generate bokeh widgets for parameterized objects'

import parambokeh
version = release = str(parambokeh.__version__)

html_static_path += ['_static']
html_theme = 'sphinx_ioam_theme'
html_theme_options = {
    'logo':'param-logo.png',
    'favicon':'favicon.ico',
#    'css':'parambokeh.css'
}

_NAV =  (
    ('Getting Started', 'getting_started/index'),
    ('User Guide', 'user_guide/index'),
    ('FAQ', 'FAQ'),
    ('About', 'about')
)

html_context.update({
    'PROJECT': project,
    'DESCRIPTION': description,
    'AUTHOR': authors,
    'WEBSITE_URL': 'https://ioam.github.io/parambokeh',
    'VERSION': version,
    'NAV': _NAV,
    'LINKS': _NAV,
    'SOCIAL': (
        ('Gitter', '//gitter.im/ioam/holoviews'),
        ('Twitter', '//twitter.com/holoviews'),
        ('Github', '//github.com/ioam/parambokeh'),
    )
}
