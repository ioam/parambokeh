import os
if "PYCTDEV_ECOSYSTEM" not in os.environ:
    os.environ["PYCTDEV_ECOSYSTEM"] = "conda"

from pyctdev import *  # noqa: api


############################################################
# Website building tasks; will move out to pyct

def task_docs():
    return {'actions': [
        'nbsite generate-rst --org ioam --project parambokeh --repo parambokeh --examples-path examples --doc-path doc',
        'nbsite build --what=html --examples-path=examples --doc-path=doc --output=./builtdocs',
        'touch ./builtdocs/.nojekyll',
        'nbsite_cleandisthtml.py ./builtdocs take_a_chance']}
