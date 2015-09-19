#!/usr/bin/env python
import os, sys
import subprocess
import cPickle as Pickle
import json
from datetime import datetime
import tempfile

#from useless.base.path import path
from unipath.path import Path as path
from unipath import FILES, DIRS, LINKS


PREFIX = "https://raw.githubusercontent.com/papers-we-love/papers-we-love/master"

def get_files(directory):
    here = path.cwd()
    directory = path(directory)
    os.chdir(directory)
    walker = directory.walk(filter=FILES)
    files = [p.relative() for p in walker if not p.relative().startswith('.')]
    os.chdir(here)
    return files

def add_file_to_annex(filename):
    url = os.path.join(PREFIX, filename)
    dirname = os.path.dirname(filename)
    annexdir = os.path.join('papers-we-love', dirname)
    if not os.path.isdir(annexdir):
        os.makedirs(annexdir)
    filename = os.path.join(annexdir, os.path.basename(filename))
    if not os.path.islink(filename):
        print "Adding", filename, "to ANNEX"    
        cmd = ['git-annex', 'addurl', '--file', filename, url]
        subprocess.check_call(cmd)
        

def add_file_to_git(filename, clone_directory):
    orig = os.path.join(clone_directory, filename)
    dirname = os.path.dirname(filename)
    annexdir = os.path.join('papers-we-love', dirname)
    if not os.path.isdir(annexdir):
        os.makedirs(annexdir)
    filename = os.path.join(annexdir, os.path.basename(filename))
    if not os.path.isfile(filename):
        cmd = ['cp', '-a', str(orig), filename]
        subprocess.check_call(cmd)
        print "Adding", filename
        cmd = ['git', 'add', filename]
        subprocess.check_call(cmd)

def add_file_to_repo(filename, clone_directory):
    if filename.endswith('.md'):
        add_file_to_git(filename, clone_directory)
    else:
        add_file_to_annex(filename)
        
def main(directory):
    if not os.path.isdir('.git/annex/'):
        raise RuntimeError, "Run this from the annex toplevel"
    files = list(get_files(directory))
    print "%d files" % len(files)
    for filename in files:
        add_file_to_repo(filename, directory)
        
    
if __name__ == '__main__':
    pwl_local_directory = path('/tmp/papers-we-love')
    if not os.path.isdir(pwl_local_directory):
        repo = 'https://github.com/papers-we-love/papers-we-love.git'
        cmd = ['git', 'clone', repo, pwl_local_directory]
        subprocess.check_call(cmd)
    if not os.path.isdir(pwl_local_directory):
        raise RuntimeError, "bad clone"
    main(pwl_local_directory)
