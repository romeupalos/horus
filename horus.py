#!/usr/bin/python

import hashlib
import os
import signal
import sys
import urllib2
from optparse import OptionParser

USER_AGENT = "SubDB/1.0 (horus/0.1; http://www.github.com/romeupalos/horus)"
API_URL = "http://api.thesubdb.com/"
EXTENSIONS = {'.mp4', '.mkv', '.avi'}


# this hash function receives the name of the file and returns the hash code
def get_hash(name):
    read_size = 64 * 1024
    with open(name, 'rb') as f:
        data = f.read(read_size)
        f.seek(-read_size, os.SEEK_END)
        data += f.read(read_size)
    return hashlib.md5(data).hexdigest()


def signal_handler(signal, frame):
    exit(0)


def check_file_size(target_file):
    try:
        file_size = os.path.getsize(target_file)
    except OSError as e:
        print "Error: (" + repr(e.errno) + ") ", e
        return False

    if file_size < (128 * 1024):
        return False
    else:
        return True


def download_sub(videofile, yes_to_all, no_to_all, language):
    if not check_file_size(videofile):
        print "File is too small"
        return 1

    hash = get_hash(videofile)
    print "hash is: " + hash

    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', USER_AGENT)]
    try:
        conn = opener.open(API_URL + "?action=search&hash=" + hash)
    except urllib2.HTTPError as e:
        print repr(e.code) + ": " + e.reason
        return 2

    response = conn.read()
    print "available languages: " + response

    if response.find(language) == -1:
        print "language is not available"
        return 3

    try:
        conn = opener.open(API_URL + "?action=download&hash=" + hash + "&language=" + language)
    except urllib2.HTTPError as e:
        print repr(e.code) + ": " + e.reason
        return 4

    filename = os.path.splitext(videofile)[0] + ".srt"

    if os.path.isfile(filename):
        if yes_to_all:
            resp = 'y'
        else:
            resp = 'n'
        if not yes_to_all and not no_to_all:
            sys.stdout.write("Error: subtitle already exists. Overwrite? (y/N): ")
            resp = sys.stdin.readline()
        if resp[0] != 'y':
            print "Skipping: File exists.\n"
            return 5

    try:
        sub_file = open(filename, 'w')
    except IOError as e:
        print "error creating file: ", e
        return 6

    sub_file.write(conn.read())
    sub_file.close()

    print filename + " downloaded\n"
    return 0


# Capture Ctrl + C (SIGINT)
signal.signal(signal.SIGINT, signal_handler)
parser = OptionParser()

parser.add_option("-y",
                  "--yes-to-all",
                  action="store_true",
                  dest="yesToAll",
                  default=False,
                  help="Overwrite without asking.")

parser.add_option("-n",
                  "--no-to-all",
                  action="store_true",
                  dest="noToAll",
                  default=False,
                  help="Don't overwrite any file")

parser.add_option("-i",
                  "--ignore-ext",
                  action="store_true",
                  dest="ignoreExtension",
                  default=False,
                  help="Ignore known video file extensions")

parser.add_option("-l",
                  "--language",
                  metavar="LANGUAGE",
                  dest="language",
                  default='pt',
                  help="language to download")

(options, args) = parser.parse_args()

if len(args) < 1:
    print "Missing files."
    exit(1)

subCount = 0

for videofile in args:
    fileext = os.path.splitext(videofile)[1]
    if options.ignoreExtension is True or fileext in EXTENSIONS:
        print "Downloading subs for " + videofile
        if download_sub(videofile, options.yesToAll, options.noToAll, options.language) == 0:
            subCount += 1
    else:
        print "Skipping " + videofile + " because " + fileext + " is not a video file\n"

print "All done; " + repr(subCount) + " subtitles downloaded"
