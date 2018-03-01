from pyct import *

# The aim would be to not have anything much here, but right now
# that's not easy because of awkward installation/specification of
# dependencies across projects.


def task_all_tests():
    return {'actions': [],
            'task_dep': ['lint','nb_lint','nb_tests']}

# TODO: move command to pyct and read deps from setup.py extras_require['docs']
def task_install_doc_dependencies():
    return {
        'actions': ['conda install -y -c pyviz/label/dev -c conda-forge nbsite sphinx_ioam_theme']}

def task_docs():
    # TODO: could do better than this, or nbsite could itself use doit
    # (providing a dodo file for docs, or using doit internally).
    return {'actions': [
        'nbsite_nbpagebuild.py ioam parambokeh ./examples ./doc',
        'sphinx-build -b html ./doc ./doc/_build/html',
        'nbsite_fix_links.py ./doc/_build/html',
        'touch ./doc/_build/html/.nojekyll',
        'nbsite_cleandisthtml.py ./doc/_build/html take_a_chance']}
