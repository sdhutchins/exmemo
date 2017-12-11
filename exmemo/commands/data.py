#!/usr/bin/env python3

import subprocess
from . import cli
from .. import Workspace
from pathlib import Path
from pprint import pprint

@cli.priority(10)
def sync():
    """\
    Import data into the project from any available source.

    Usage:
        exmemo [data] sync [-v]

    Options:
        -v --verbose
            Print out each command that is run to sync the data.

    You have lots of control over how exmomo finds and imports data.  The basic 
    idea is to define "data collectors" by adding [[data]] sections any of your  
    configuration files.  Each of these sections should contain a type and any 
    options specific to that type, e.g.:

        [[data]]
        type = ...
        this_option = ...
        that_option = ...

    The type specifies the algorithm that will be used to find and import files.  
    The following types are currently installed:

    {installed_collectors}

    If none of these collectors can handle the data you want to sync, it's easy to 
    write your own.  Each collector is just a class that adheres to the following 
    interface:

       class MyCollector:
           \"\"\"
           Description of options...
           \"\"\"
       
           def __init__(self, this_option, that_option):
              pass

           def sync(self, workspace, verbose):
              pass

    The docstring is used to populate this usage document.  The arguments to the 
    constructor define the options that the collector understands.  The sync() 
    method does the actual work of syncing the data.  The workspace argument is an 
    object that contains information about all the paths in the project, and the 
    verbose argument is just a boolean indicating whether or not you should print 
    out every command that gets run.  Once you've written a class according to this 
    interface, register it with the 'exmemo.datacollectors' entry point via the 
    setuptools plugin API, and it'll be available to use.
    """
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd()

    # Add usage text for each collector to the docstring.
    #from ..collectors import get_collectors

    work.sync_data(args['--verbose'])

@cli.priority(10)
def link():
    """
    Make a symbolic link to the indicated data file.

    Usage:
        exmemo [data] link <substr> [<dir>]

    Arguments
        <substr>
            A string specifying the data file to link.  You can provide any 
            substring from the name of the data file.  If the substring is not 
            unique, you'll be asked which file you meant.

        <dir>
            The directory where the link will be created.  By default, this is 
            the current working directory ('.').
            
    This command is most commonly used to link data files into particular 
    experiments in the notebook directory.  Thus the data directory is a 
    repository for all of your data, and the notebook directory is a curated 
    set of only the most important or relevant data.
    """
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd()
    data = work.pick_data(args['<substr>'])
    link = Path(args['<dir>'] or '.') / data.name

    link.symlink_to(data)

def gel():
    """
    Format a gel for inclusion in the lab notebook.  In particular, this means 
    converting it from a *.tif to a *.png, inverting it's colors, and giving 
    you a chance to crop it.

    Usage:
        exmemo data gel <substr> [<dir>] [-f]

    Arguments:
        <substr>
            A string specifying the data file to copy and crop.  You can 
            provide any substring from the name of the data file.  If the 
            substring is not unique, you'll be asked which file you meant.

        <dir>
            The directory where the image will be copied.  By default, this is 
            the current working directory ('.').

    Options:
        -f, --force
            Overwrite any existing image.

    This command is commonly used to copy gels into the notebook directory.  
    The full resolution images stay in the data directory, but you can make a 
    nicely formatted copy to show in the notebook.
    """
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd()
    data = work.pick_data(args['<substr>'])
    copy = Path(args['<dir>'] or '.') / f'{data.stem}.png'

    if copy.exists() and not args['--force']:
        raise FileAlreadyExists(copy)

    convert = 'convert', str(data), '-fill', 'white', '-opaque', 'red', '-negate', str(copy)
    gimp = 'gimp', str(copy)

    subprocess.run(convert)
    subprocess.Popen(gimp)

def ls():
    """\
    List data files.

    Usage:
        exmemo data ls [<substr>]

    Arguments:
        <substr>
            Only list files that contain the given substring.
    """
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd()

    for path in work.iter_data(args['<substr>']):
        print(path.relative_to(work.data_dir))


class FileAlreadyExists(Exception):
    show_message_and_die = True

    def __init__(self, path):
        self.message = f"Refusing to overwrite {path}"



