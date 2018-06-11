from setuptools import setup

# TODO:
#  - release new nbsite

# Temporary until build requirements as specified in pyproject.toml
# are widely supported
try:
    import pyctbuild
except ImportError:
    raise ImportError("Parambokeh requires pyctbuild to build; please upgrade to pip>=10 and try again (or alternatively, install pyctbuild manually first (e.g. `conda install -c pyviz pyctbuild`)")


if __name__=="__main__":

    # TODO: hope to eliminate the examples handling from here too
    # (i.e. all lines except setup()), moving it to pyctbuild
    import os, sys, shutil
    example_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'parambokeh','examples')
    if 'develop' not in sys.argv:
        import pyctbuild.examples
        pyctbuild.examples.examples(example_path, __file__, force=True)
    
    setup()

    if os.path.isdir(example_path):
        shutil.rmtree(example_path)
