# just dumping everything in here for now; will sort out later

import os

########## autover ##########

def embed_version(basepath, ref='v0.2.2'):
    """
    Autover is purely a build time dependency in all cases (conda and
    pip) except for when you use pip's remote git support [git+url] as
    1) you need a dynamically changing version and 2) the environment
    starts off clean with zero dependencies installed.
    This function acts as a fallback to make Version available until
    PEP518 is commonly supported by pip to express build dependencies.
    """
    import io, zipfile, importlib
    try:    from urllib.request import urlopen
    except: from urllib import urlopen
    try:
        url = 'https://github.com/ioam/autover/archive/{ref}.zip'
        response = urlopen(url.format(ref=ref))
        zf = zipfile.ZipFile(io.BytesIO(response.read()))
        ref = ref[1:] if ref.startswith('v') else ref
        embed_version = zf.read('autover-{ref}/autover/version.py'.format(ref=ref))
        with open(os.path.join(basepath, 'version.py'), 'wb') as f:
            f.write(embed_version)
        return importlib.import_module("version")
    except:
        return None

def get_setup_version(reponame):
    """
    Helper to get the current version from either git describe or the
    .version file (if available).
    """
    import json
    basepath = os.path.split(__file__)[0]
    version_file_path = os.path.join(basepath, reponame, '.version')
    try:
        from param import version
    except:
        raise
        version = embed_version(basepath)
    if version is not None:
        return version.Version.setup_version(basepath, reponame, archive_commit="$Format:%h$")
    else:
        print("WARNING: param>=1.6.0 unavailable. If you are installing a package, this warning can safely be ignored. If you are creating a package or otherwise operating in a git repository, you should install param>=1.6.0.")
        return json.load(open(version_file_path, 'r'))['version_string']


########## examples ##########

import shutil

def examples(path, root, verbose=False, force=False):
    """
    Copies the notebooks to the supplied path.
    """
    filepath = os.path.abspath(os.path.dirname(root))
    example_dir = os.path.join(filepath, './examples')
    if not os.path.exists(example_dir):
        example_dir = os.path.join(filepath, '../examples')
    if os.path.exists(path):
        if not force:
            print('%s directory already exists, either delete it or set the force flag' % path)
            return
        shutil.rmtree(path)
    ignore = shutil.ignore_patterns('.ipynb_checkpoints', '*.pyc', '*~')
    tree_root = os.path.abspath(example_dir)
    if os.path.isdir(tree_root):
        shutil.copytree(tree_root, path, ignore=ignore, symlinks=True)
    else:
        print('Cannot find %s' % tree_root)



def default_setup_args():

    ########## setup.py "best practice" ##########
    
    args = {
        'include_package_data':True,
        'long_description_content_type':"text/markdown",
        'license':'BSD-3',
        'classifiers': [
            "License :: OSI Approved :: BSD License",
            "Operating System :: OS Independent"
        ]
    }

    from setuptools import find_packages
    args['packages'] = find_packages()
    args['long_description']=open('README.md').read()

    # + could check manifest.in entries


    
    ########## common pyviz setup.py metadata ##########

    # would want to make this configurable. And moving it out of individual setup.py
    # files might annoy people who are trying to read setup.py by eye

    AUTHOR = "pyviz"
    AUTHOR_EMAIL = "holoviews@gmail.com"
    PLATFORMS = ["Windows","MacOS","Linux"]

    args.update({
        'author': AUTHOR,
        'author_email': AUTHOR_EMAIL,
        'maintainer': AUTHOR,
        'maintainer_email': AUTHOR_EMAIL,
        'platforms': PLATFORMS,
    })


    return args


# TODO: seems like setuptools doesn't support all things that can be in PKG-INFO,
# like multiple URLs, so (for example) can't get link to github and homepage from pypi
# https://www.python.org/dev/peps/pep-0566/ https://packaging.python.org/specifications/core-metadata/#project-url-multiple-use .
# Should come with pyproject/switching to different build system e.g. flit
