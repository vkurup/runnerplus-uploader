#! /usr/bin/env python

import glob
import urllib
import os
from os.path import join
import subprocess

# Edit these values
login_name = "youremail@example.com"
login_pass = "yourpassword"

# Don't edit these values
url = "http://www.runnerplus.com/"
widget_version = "0.01"
found_ipod = False

debug = True
testing = False

def push_data():
    global found_ipod
    xmlfile = None

    uid = validate_user()
    if debug: print "uid == %s." % uid
    if uid == "0":
        raise StandardError("authentication failed")
    
    mount_point = get_ipod_mount()
    path = join(mount_point, "iPod_Control", "Device", "Trainer", "Workouts", "Empeds")
    if os.path.isdir(path):
        stats = os.statvfs(path)
        total_space = (stats[2] * stats[0]) / (1024 * 1024)
        avail_space = (stats[4] * stats[0]) / (1024 * 1024)
        print "iPod mounted at %s has a capacity of %d MB and has %d MB available" % \
            (mount_point, total_space, avail_space)

        filelist = glob.glob(join(path, '*', '*', '*-*.xml'))
        for xmlfile in filelist:
            if debug: print "debug found: " + xmlfile
            post_to_runnerplus(uid, xmlfile)
        found_ipod = True

def post_to_runnerplus(uid, fullpath):
    f = open(fullpath)
    data = f.read()
    f.close()
    v = "Python uploader " + widget_version + " (Linux)"
    post_data = urllib.urlencode({'uid' : uid, 'v' : v, 'data' : data })
    post_url = url + "profile/api_postdata.asp"
    if not testing: 
        contents = urllib.urlopen(post_url, post_data).read()
    else:
        contents = "Testing"

    if debug: print contents
    
def version_check():
    print "checking for updates to script..."
    #sock = urllib.urlopen(url + "profile/api_version.asp")
    #htmlSource = sock.read()
    #sock.close()
    #print htmlSource
    return "0.01"

def validate_user():
    n = login_name
    p = login_pass
    new_version = version_check()
    if new_version > widget_version:
        print "A new version of this script is now available. Please download it."
    if debug: print "validating user " + n + "..."
    user_url = url + "profile/api_validateuser.asp"
    post_data = urllib.urlencode({'n' : n, 'p' : p })
    if not testing:
        contents = urllib.urlopen(user_url, post_data)
        uid = contents.read()
    else:
        uid = "999"
    return uid

def get_ipod_mount():
    """Search all mounted volumes for device which has NikePlus data"""
    output = subprocess.Popen(['/bin/df','-P','-x','tmpfs'],stdout=subprocess.PIPE).communicate()[0]
    devices = output.split('\n')[1:]
    for line in devices:
        if line:
            mount = line.split()[5]
            nike = join(mount, "iPod_Control", "Device", "Trainer", "Workouts", "Empeds")
            if os.path.exists(nike):
                return mount

    raise StandardError("failed to find iPod-NikePlus file system in any filesystem")

if __name__ == "__main__":
    push_data()
    if found_ipod:
        print "Successfully synced to runnerplus"
    else:
        print "Sync was unsuccessful"
