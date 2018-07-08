# -*- coding: utf-8 -*-

from nbsite.shared_conf import *

project = u'ParamBokeh'
authors = u'ParamBokeh contributors'
copyright = u'2017 ' + authors
description = 'Generate Bokeh widgets for Parameterized objects'

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
    ('User Guide', 'user_guide/index'),
    ('FAQ', 'FAQ'),
    ('About', 'about')
)

html_context.update({
    'PROJECT': project,
    'DESCRIPTION': description,
    'AUTHOR': authors,
    'WEBSITE_URL': 'https://parambokeh.pyviz.org',
    'VERSION': version,
    'NAV': _NAV,
    'LINKS': _NAV,
    'SOCIAL': (
        ('Gitter', '//gitter.im/ioam/holoviews'),
        ('Github', '//github.com/ioam/parambokeh'),
    )
})

nbbuild_patterns_to_take_along = ["simple.html"]
