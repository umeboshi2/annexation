import os
import sys
import ConfigParser
import cPickle as Pickle
import time
import random
import json
import subprocess

import pytumblr

def make_client(config):
    apikey = config.get('main', 'api_key')
    apisecret = config.get('main', 'api_secret')
    token = config.get('main', 'token')
    token_secret = config.get('main', 'token_secret')
    return pytumblr.TumblrRestClient(apikey, apisecret, token, token_secret)


def get_photos_from_post(post):
    photos = list()
    #import pdb ; pdb.set_trace()
    for ph in post['photos']:
        orig = ph['original_size']
        photos.append(orig['url'])
    return photos

def get_photos_from_posts(posts):
    photos = list()
    for post in posts['posts']:
        if post['type'] == 'photo':
            pphotos = get_photos_from_post(post)
            photos += pphotos
    return photos

def get_photos_from_list_of_posts(plist):
    photos = list()
    for post in plist:
        if post['type'] == 'photo':
            pphotos = get_photos_from_post(post)
            #photos += pphotos
            photos.append(dict(post=post, photos=pphotos))
    return photos
    
def add_photos_to_annex(photos, annexdir, blogdir=None):
    merge_annex = False
    here = os.getcwd()
    os.chdir(annexdir)
    if blogdir is not None:
        if not os.path.isdir(blogdir):
            os.makedirs(blogdir)
        os.chdir(blogdir)
    for pdata in photos:
        url_count = 0
        for url in pdata['photos']:
            url_count +=1
            cmd = ['git-annex', 'addurl',
                   '-c', 'annex.alwayscommit=false']
            if blogdir is not None:
                ext = url.split('.')[-1]
                filename_tmpl = '%016d-%02d.%s'
                filename = filename_tmpl % (pdata['post']['id'], url_count, ext)
                cmd += ['--file', filename]
                cmd.append(url)
            if os.path.islink(filename):
                print "%s already exists, skipping." % filename
                continue
            try:
                subprocess.check_call(cmd)
                merge_annex = True
            except subprocess.CalledProcessError, e:
                print e
    if merge_annex:
        print "Merging...."
        cmd = ['git-annex', 'merge']
        subprocess.check_call(cmd)
    os.chdir(here)

            
                      
# get all posts when total_desired is None
def get_posts(client, blogname, total_desired=None, offset=0, limit=20):
    current_post_count = 0
    posts = client.posts(blogname, offset=offset, limit=limit)
    if 'total_posts' not in posts:
        return list()
    total_post_count = posts['total_posts'] - offset
    if total_desired is not None:
        if total_desired > total_post_count:
            print "Too many posts desired."
            total_desired = total_post_count
        total_post_count = total_desired
    all_posts = list()
    these_posts = posts['posts']
    if len(these_posts) != limit:
        if len(these_posts) != total_post_count:
            msg = "Too few posts: %d" % len(these_posts)
            raise RuntimeError, msg
    while current_post_count < total_post_count:
        ignored_post_count = 0
        batch_length = len(these_posts)
        while len(these_posts) and total_post_count:
            post = these_posts.pop()
            current_post_count += 1
            all_posts.append(post)
        offset += limit
        print "Getting from tumblr at offset %d" % offset
        posts = client.posts(blogname, offset=offset, limit=limit)
        these_posts = posts['posts']
        remaining = total_post_count - current_post_count
        print "%d posts remaining for %s." % (remaining, blogname)        
    return all_posts


def get_blog_photos(client, blogname, total_desired=None, offset=0, limit=20):
    print "Get_Blog_Photos for %s" % blogname
    bposts = get_posts(client, blogname, total_desired=total_desired,
                       offset=offset, limit=limit)
    photos = get_photos_from_list_of_posts(bposts)
    return photos



if __name__ == '__main__':
    import pdb
    here = os.getcwd()
    blogdir = os.path.join(here, 'blogs')
    
    config = ConfigParser.ConfigParser()
    creds_filename = '.creds'
    if not os.path.isfile(creds_filename):
        raise RuntimeError, "unable to find %s" % creds_filename
    config.read([creds_filename])
    c = make_client(config)
    info = c.info()
    user = info['user']
    username = user['name']

    if len(sys.argv) < 2:
        raise RuntimeError, "Need name of blog"
    blogname = sys.argv[1]
    total_desired = None
    if len(sys.argv) == 3:
        total_desired = int(sys.argv[2])
    pfilename = 'current-%s.pickle' % blogname
    if os.path.isfile(pfilename):
        bp = Pickle.load(file(pfilename))
    else:
        bp = get_blog_photos(c, blogname, total_desired=total_desired)
        with file(pfilename, 'w') as outfile:
            Pickle.dump(bp, outfile)
    add_photos_to_annex(bp, blogdir, blogname)
    os.rename(pfilename, '%s.orig' % pfilename)
    
    
    #bposts = get_posts(c, 'libutron', total_desired=50)
    #pp = get_blog_photos(c, 'libutron')
    #bp = get_blog_photos(c, 'libutron', total_desired=100)
    #add_photos_to_annex(bp, urldir)
    #add_photos_to_annex(bp, blogdir, 'libutron')
    
