#!/usr/bin/python

import hashlib
import os
import signal
import sys
import urllib2
import mimetypes
from optparse import OptionParser

USER_AGENT = "SubDB/1.0 (horus/0.1; http://www.github.com/romeupalos/horus)"
API_URL = "http://api.thesubdb.com/"


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
            print "Skipping: File exists."
            return 5

    try:
        sub_file = open(filename, 'w')
    except IOError as e:
        print "error creating file: ", e
        return 6

    sub_file.write(conn.read())
    sub_file.close()

    print filename + " downloaded"
    return 0

def isVideo(path):
    mime_type = mimetypes.guess_type(path)[0]
    if mime_type is not None:
        return mime_type.split('/')[0] == 'video'
    return False

def download_sub_recursive(path):
    if os.path.isdir(path):
        for f in os.listdir(path):
            download_sub_recursive(os.path.join(path, f))
    else:
        fileext = os.path.splitext(path)[1]
        if options.ignoreMimeType is True or isVideo(path):
            print "Downloading subs for " + os.path.basename(path)
            download_sub(path, options.yesToAll, options.noToAll, options.language)
        else:
            print "Skipping " + path

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
                  "--ignore-mime",
                  action="store_true",
                  dest="ignoreMimeType",
                  default=False,
                  help="Download subtitles for non video files")

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

for path in args:
    download_sub_recursive(path)

print "All done;"
