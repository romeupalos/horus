#!/usr/bin/python

import hashlib
import os
import signal
import sys
import urllib2
import mimetypes
import pysrt
from optparse import OptionParser

USER_AGENT = "SubDB/1.0 (horus/0.1; http://www.github.com/romeupalos/horus)"
API_URL = "http://api.thesubdb.com/"

ADS_WORDS = ['opensubtitles', 'legendei.com', 'sfdownload.com']

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

def remove_ads_and_save(sub_contents, path):
    sub_contents = sub_contents.decode('iso-8859-15')
    srt_sub = pysrt.from_string(sub_contents)

    index = 0
    while index < len(srt_sub):
        srt_sub[index].index = index + 1

        sub_item = srt_sub[index]
        if True in [True for word in ADS_WORDS if word in sub_item.text.lower()]:
            del srt_sub[index]
        else:
            index += 1
    srt_sub.save(path, encoding='utf-8')


def download_sub(videofile, overwrite, language, keep_ads):
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

    # language as None means to download all languages available
    if language is None:
        for available_language in response.split(','):
            download_sub_for_language(opener, videofile, hash, overwrite, available_language, keep_ads)

    # Download if for desired language
    else :
        if response.find(language) == -1:
            print "language is not available"
            return 3

        download_sub_for_language(opener, videofile, hash, overwrite, language, keep_ads)


def download_sub_for_language(opener, videofile, hash, overwrite, language, keep_ads):
    try:
        conn = opener.open(API_URL + "?action=download&hash=" + hash + "&language=" + language)
    except urllib2.HTTPError as e:
        print repr(e.code) + ": " + e.reason
        return 4

    sub_filename = os.path.splitext(videofile)[0] + "." + language + ".srt"

    # Check if the file exists
    if os.path.isfile(sub_filename):
        if overwrite is True:
            resp = 'y'
        elif overwrite is False:
            resp = 'n'
        else:
            sys.stdout.write("Error: subtitle already exists. Overwrite? (y/N): ")
            resp = sys.stdin.readline()

        if resp[0] is not 'y':
            print "Skipping %s: File exists." % sub_filename
            return 5

    if keep_ads:
        with open(sub_filename, 'w') as sub_file:
            sub_file.write(conn.read())
    else:
        remove_ads_and_save(conn.read(), sub_filename)

    print sub_filename + " downloaded"
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

            # None language tells the script to download All Languages
            language = None if options.all_languages else options.language

            overwrite = True if options.yesToAll else False if options.noToAll else None

            download_sub(path, overwrite, language, options.keep_ads)
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

parser.add_option("-a",
                  "--all-languages",
                  metavar="ALL_LANGUAGES",
                  dest="all_languages",
                  default=False,
                  action="store_true",
                  help="download all languages")

parser.add_option("-k",
                  "--keep-ads",
                  metavar="KEEP_ADS",
                  dest="keep_ads",
                  default=False,
                  action="store_true",
                  help="don't remove ads from subtitles")

(options, args) = parser.parse_args()

if len(args) < 1:
    print "Missing files."
    exit(1)

for path in args:
    download_sub_recursive(path)

print "All done;"
