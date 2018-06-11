import os
import sys
import shutil

from setuptools import setup

# TODO:
#  - release new nbsite
#  - replace (param build time dep + _pyct_setup_support) with pyctbuild


# Temporary until build requirements as specified in pyproject.toml
# are widely supported
try:
    # this list will become pyctbuild (and autover, unless autover is
    # included in pyctbuild)
    import param # noqa
    import _pyct_setup_support as pss
except ImportError as e:
    raise ImportError("requires param,... to ... please first install param (e.g. pip install param) or upgrade to pip>=10 or conda-build>= ?")


if __name__=="__main__":

    # TODO: hope to eliminate the examples handling from here too
    # (i.e. all lines except setup()), moving it to pyctbuild
    
    example_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'parambokeh','examples')
    if 'develop' not in sys.argv:
        pss.examples(example_path, __file__, force=True)
    
    setup()

    if os.path.isdir(example_path):
        shutil.rmtree(example_path)
