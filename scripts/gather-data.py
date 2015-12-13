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

# apt-get install python-regex
import regex


PREFIX = "https://raw.githubusercontent.com/papers-we-love/papers-we-love/master"
# FIXME - make better regex to remove [] and ()
URL_REGEX = "(?|(?<txt>\[.+?\])(?<url>\(.+?\)))"

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

def parse_markdown(filename, clone_directory):
    orig = os.path.join(clone_directory, filename)
    dirname = os.path.dirname(filename)
    annexdir = os.path.join('papers-we-love', dirname)
    annexfile = os.path.join(annexdir, os.path.basename(filename))
    data = file(annexfile).read()
    result = regex.findall(URL_REGEX, data)
    for match in result:
        txt = match[0][1:-1].replace(' ', '_')
        url = match[1][1:-1]
        if url.endswith('.pdf'):
            txt = '%s.pdf' % txt
        fname = os.path.join(annexdir, txt)
        if not os.path.isfile(fname):
            print fname, url
            cmd = ['git-annex', 'addurl', '--file', fname, url]
            subprocess.call(cmd)
    #import pdb ; pdb.set_trace()
    #with file(annexfile) as infile:
    #    for line in infile:
    #        pass

def markdown_has_papers(filename, clone_directory):
    if filename.startswith('_meetups/') or filename == 'README.md':
        return False
    no_papers = ['CODE_OF_CONDUCT.md', '2014_meetups.md']
    basename = os.path.basename(filename)
    return basename not in no_papers
    
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
        if filename.endswith('.md'):
            #print "Checking", filename
            if markdown_has_papers(filename, directory):
                #print "%s should have papers" % filename
                parse_markdown(filename, directory)
    
if __name__ == '__main__':
    pwl_local_directory = path('/tmp/papers-we-love')
    if not os.path.isdir(pwl_local_directory):
        repo = 'https://github.com/papers-we-love/papers-we-love.git'
        cmd = ['git', 'clone', repo, pwl_local_directory]
        subprocess.check_call(cmd)
    if not os.path.isdir(pwl_local_directory):
        raise RuntimeError, "bad clone"
    cmd = ['git', '-C', '/tmp/papers-we-love', 'pull']
    subprocess.check_call(cmd)
    main(pwl_local_directory)
