import os
import sys
import shutil

from setuptools import setup

# TODO:
#  - release new nbsite
#  - replace (param build time dep + _pyct_setup_support) with pyctbuild


try:
    # this list will become pyctbuild (and autover, unless autover is included in pyctbuild)
    import param # noqa
    import _pyct_setup_support as pss
except ImportError as e:
    raise ImportError("requires param,... to ... please first install param (e.g. pip install param) or upgrade to pip>=10 or conda-build>= ?")



install_requires = [
    'param >=1.6.1',
    'bokeh >=0.12.10',
    'pyviz_comms'
]

extras_require = {
    'tests': [
        'nbsmoke >=0.2.6',
        'flake8',
        'pytest >=2.8.5'
    ],
    'examples': [
        'pyct',
        'holoviews >=1.9.0',
        'pandas',
        'jupyter',
        'pyparsing', # ???
    ]
}

extras_require['doc'] = extras_require['examples'] + [
    'nbsite',
    'sphinx_ioam_theme'
]

extras_require['all'] = sorted(set(sum(extras_require.values(), [])))

setup_args = pss.default_setup_args()

setup_args.update(dict(
    name='parambokeh',
    version= pss.get_setup_version("parambokeh"),
    python_requires = '>=2.7',
    install_requires = install_requires,
    extras_require = extras_require,
    tests_require = extras_require["tests"],
    url = 'https://github.com/ioam/parambokeh',
    description='ParamBokeh provides an easy way to generate a UI for param based classes in the notebook or on bokeh server.',
    entry_points={
        'console_scripts': [
            'parambokeh = parambokeh.__main__:main'
        ]
    }    
))


if __name__=="__main__":

    # TODO: hope to eliminate the examples handling from here too, moving it to pyctbuild
    ###
    example_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'parambokeh','examples')
    if 'develop' not in sys.argv:
        pss.examples(example_path, __file__, force=True)
    ###
    
    setup(**setup_args)

    ### examples handling
    if os.path.isdir(example_path):
        shutil.rmtree(example_path)
    ###
