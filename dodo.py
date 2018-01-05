DOIT_CONFIG = {'verbosity': 2}

from ioamdoit import (task_download_miniconda, task_install_miniconda,
                      task_create_env)

# The aim would be to not have anything much here, but right now
# that's not easy because of awkward installation/specification of
# dependencies across projects.

def task_install_required_dependencies():
    return {'actions': ['conda install -y -q -c conda-forge param "bokeh>=0.12.10"']}

def task_install_test_dependencies():
    return {
        'actions': [
            'conda install -y -q -c conda-forge "holoviews>=1.9.0" pandas notebook flake8 pyparsing pytest',
            'pip install pytest-nbsmoke'],
        'task_dep': ['install_required_dependencies']
        }

def task_install_doc_dependencies():
    # would not need to exist if nbsite had conda package
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
    # TODO: could do better than this, or nbsite could itself use doit
    # (providing a dodo file for docs, or using doit internally).
    return {'actions': [
        'nbsite_nbpagebuild.py ioam parambokeh ./examples ./doc',
        'sphinx-build -b html ./doc ./doc/_build/html',
        'nbsite_fix_links.py ./doc/_build/html',
        'touch ./doc/_build/html/.nojekyll',
        'nbsite_cleandisthtml.py ./doc/_build/html take_a_chance']}
