# First section is general (could be in e.g. a submodule shared across
# projects), second section is specific to this project.

################################################################################
## general

import glob
import platform
import os
import sys
import zipfile
try:
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve

miniconda_url = {
    "Windows": "https://repo.continuum.io/archive/Miniconda3-latest-Windows-x86_64.exe",
    "Linux": "https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh",
    "Darwin": "https://repo.continuum.io/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
}

def task_install_miniconda():
    # requires python already :S

    # TODO: location param passing e.g. "doit install_miniconda --location
    # /tmp/123" not working
    location = {
        'name':'location',
        'long':'location',
        'short':'l',
        'type':str,
        'default':os.path.abspath(os.path.expanduser('~/miniconda'))}

    url = miniconda_url[platform.system()]
    miniconda_installer = url.split('/')[-1]

    def download_miniconda(targets):
        urlretrieve(url,miniconda_installer)

    yield {'name': 'download_miniconda',
           'actions': [download_miniconda]}

    if platform.system() == "Windows":
        yield {
            'name': platform.system(),
            'params':[location],
            'actions': ['START /WAIT %s'%miniconda_installer + " /S /AddToPath=0 /D=%(location)s"]
        }
    elif platform.system() in ("Linux","Darwin"):
        yield {
            'name': platform.system(),
            'params':[location],
            'actions': ["bash %s"%miniconda_installer + " -b -p %(location)s"]
        }
    else:
        raise Exception("%s not in %s"%(platform.system(),miniconda_url.keys()))


def task_create_env():
    python = {
        'name':'python',
        'long':'python',
        'type':str,
        'default':'3.6'}

    env = {
        'name':'name',
        'long':'name',
        'type':str,
        'default':'test-environment'}

    return {
        'params': [python,env],
        'actions': ["conda create -y --name %(name)s python=%(python)s"]}


################################################################################
## special to this project

def task_install_required_dependencies():
    return {'actions': ['conda install -y -q -c conda-forge param "bokeh>=0.12.10"']}

def task_install_test_dependencies():
    return {
        'actions': [
            'conda install -y -q "holoviews>=1.9.0" pandas notebook flake8 pyparsing pytest',
            'pip install pytest-nbsmoke'],
        'task_dep': ['install_required_dependencies']
        }

def task_install_doc_dependencies():
    # might not exist if nbsite had conda package
    return {
        'actions': [
            'conda install -y -q -c conda-forge notebook ipython sphinx beautifulsoup4 graphviz selenium phantomjs',
            'pip install nbsite sphinx_ioam_theme'],
        'task_dep': ['install_test_dependencies']
        }

def task_lint():
    return {'actions': [
        'flake8 --ignore E,W parambokeh',
        'pytest --nbsmoke-lint examples/']}

def task_tests():
    return {'actions': [
        'pytest --nbsmoke-run examples/']}


def task_docs():
    return {'actions': [
        'nbsite_nbpagebuild.py ioam parambokeh ./examples ./doc',
        'sphinx-build -b html ./doc ./doc/_build/html',
        'nbsite_fix_links.py ./doc/_build/html',
        'touch ./doc/_build/html/.nojekyll',
        'nbsite_cleandisthtml.py ./doc/_build/html take_a_chance']}

