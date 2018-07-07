from setuptools import setup
####
# Build dependency checks
#
# Temporary, until pyproject.toml is widely supported. We're expecting
# most users to install a wheel or conda package, neither of which
# requires running setup.py and building a package.  So these checks
# are for packagers and those installing from e.g. github.
import setuptools
from pkg_resources import parse_version
missing_build_dep = False
if parse_version(setuptools.__version__)<parse_version('30.3.0'):
    missing_build_dep = True
try:
    import pyct.build
    import param 
    if parse_version(param.__version__)<parse_version('1.7.0'):
        missing_build_dep = True
except:
    missing_build_dep = True

if missing_build_dep:
    raise ValueError('Building parambokeh requires setuptools>=30.3.0, param>=1.7.0, and pyct; please upgrade to pip>=10 and try again. Alternatively, install the build dependencies manually first (e.g. `pip install --upgrade "setuptools>=30.3.0" "param>=1.7.0" pyct` or `conda install -c pyviz "setuptools>=30.3.0" "param>=1.7.0" pyct-core`)')
#####

if __name__=="__main__":
    # TODO: hope to eliminate the examples handling from here
    # (i.e. all lines except setup()), moving it to pyct
    import os, sys, shutil
    example_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'parambokeh','examples')
    if 'develop' not in sys.argv:
        pyct.build.examples(example_path, __file__, force=True)
    
    setup()

    if os.path.isdir(example_path):
        shutil.rmtree(example_path)
