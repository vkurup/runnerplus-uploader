#! /usr/bin/env python

import glob
import urllib
import os
import sys
from os.path import join
import subprocess
import ConfigParser
import shutil
import string

url = "http://www.runnerplus.com/"
script_version = 0.02
sync_successful = False
config_filename = join(os.path.expanduser("~"), ".runnerplusrc")

debug = True
testing = False

def push_data():
    xmlfile = None
    global sync_successful
    global config_filename

    # check for new versions of the script
    new_version = version_check()
    if new_version > script_version:
        print "A new version of this script is now available. Please download it."

    # read the config file
    config = ConfigParser.SafeConfigParser({'dirname': '.runnerplus'})
    config_found = config.read(config_filename)

    if not config_found:
        raise StandardError("Config File not found. See README file for instructions on creating a config file")

    email = config.get('Login','email')
    password = config.get('Login','password')
    backupdir = join(os.path.expanduser("~"), config.get('Backup', 'dirname'), 'synced')
    if debug: print "config info found for email:" + email

    uid = validate_user(email, password)
    if debug: print "uid == %s." % uid
    if uid == "0":
        raise StandardError("authentication failed")

    # create the backup directory, if not present
    if not os.path.exists(backupdir):
        if debug: print "backup dir not found, so creating it"
        os.makedirs(backupdir)
    
    mount_point = get_ipod_mount()
    if debug: print "iPod found at " + mount_point
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
            post_to_runnerplus(uid, xmlfile, backupdir)
        sync_successful = True

def post_to_runnerplus(uid, fullpath, backupdir):
    basename = os.path.basename(fullpath)
    if os.path.exists(join(backupdir, basename)):
        if debug: print "File has been previously synced: " + basename
    else:
        if debug: print "Syncing file: " + basename
        f = open(fullpath)
        data = f.read()
        f.close()

        v = "Python uploader " + str(script_version) + " (Linux)"
        post_data = urllib.urlencode({'uid' : uid, 'v' : v, 'data' : data })
        post_url = url + "profile/api_postdata.asp"
        if not testing: 
            try:
                contents = urllib.urlopen(post_url, post_data).read()
                # move to backup folder
                if debug: print "Sync successful. Back up file:" + basename
                shutil.copy(fullpath, backupdir)
            except:
                contents = sys.exc_info()[0]
                print contents
        else:
            contents = "Testing"
            
        if debug: print contents
    
def version_check():
    print "checking for updates to script..."
    sock = urllib.urlopen("http://www.kurup.org/software/runnerplus/version")
    htmlSource = sock.read()
    sock.close()
    try:
        version = string.atof(htmlSource)
    except:
        version = 0
    return version

def validate_user(email, password):
    if debug: print "validating user " + email + " ..."
    user_url = url + "profile/api_validateuser.asp"
    post_data = urllib.urlencode({'n' : email, 'p' : password })
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
    if sync_successful:
        print "Successfully synced to runnerplus"
    else:
        print "Sync was unsuccessful"
