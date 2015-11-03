#!/usr/bin/env python

import argparse
import getpass
import atexit
import sys
import time
from urlparse import urlparse

import m3u8

def get_args():
    """Get command line args from the user.
    """
    parser = argparse.ArgumentParser(
        description='Grab the various stream profile bitrates and resolutions for master m3u8 files')

    parser.add_argument('-f', '--file',
                        action='store',
                        help='File of URLs to load. This overrides a URL provided on the command-line')

    parser.add_argument('-o', '--output',
                        action='store',
                        help='Filename to write output to.')

    parser.add_argument('-a', '--append',
                        action='store_true',
                        default=False,
                        help='Append to the file given with the --output argument as opposed to overwriting the file')

    parser.add_argument('url',
                        nargs='?', default='NO_URL',
                        action='store',
                        help='The url of the master m3u8 playlist')



    args = parser.parse_args()
    if args.url == "NO_URL" and not args.file:
        print >> sys.stderr, "Error: You must either specify a URL on the command-line or provide a filename via the --file argument\n\n"
        parser.print_help()
        exit(1)

    return args
# enddef get_args()

def render_bandwidth(playlists, separator):
    bandwidth = ''
    for playlist in playlists:
        bandwidth += str(playlist.stream_info.bandwidth)
        bandwidth += separator

    return bandwidth[:-1]
# enddef render_bandwidth()

def render_resolution(playlists, separator):
    resolution_list = ''
    for playlist in playlists:
        resolution = str(playlist.stream_info.resolution)
        resolution = resolution.replace("(", "")
        resolution = resolution.replace(")", "")
        resolution = resolution.replace(" ", "")
        resolution_list += resolution.replace(",", "x")
        resolution_list += separator

    return resolution_list[:-1]
# enddef render_resolution()

def render_date_iso8601():
    timestamp = time.strftime('%Y-%m-%dT%H:%M:%S%z', time.localtime())
    return timestamp
# enddef render_date_iso8601()

def render_csv(url, playlists):
    csv = render_date_iso8601()
    csv += ','
    csv += url
    csv += ","
    csv += render_bandwidth(playlists, ",")
    csv += ","
    csv += render_resolution(playlists, ",")
    return csv
# enddef render_csv()

def get_urls(args):
    lines = []
    if args.file:
        lines = [line.strip() for line in open(args.file)]
    else:
        lines.append(args.url)

    return lines
# enddef get_urls()

def verify_url(url):
    urlcheck = urlparse(url)

    if len(urlcheck.scheme) < 1 or len(urlcheck.netloc) < 1 or len(urlcheck.path) < 1:
        return False

    return True
# enddef verify_url()

def main():
    """
    Simple command-line program for listing stream profiles of a master m3u8 playlist.
    """
    args = get_args()

    urls = get_urls(args)

    if len(urls) < 1:
        print >> sys.stderr, render_date_iso8601(), "No valid URLs to process."
        exit(1)

    outfile = None

    if args.output:
        try:
            outfile = open(args.output, 'a' if args.append == True else 'w')
        except IOError as error:
            print >> sys.stderr, render_date_iso8601(), "Error: opening file:", args.output, ">>", url


    for url in urls:
        if verify_url(url) == True:
            try:
                m3u8_obj = m3u8.load(url)
                if m3u8_obj.is_variant:
                    print >> sys.stdout if outfile is None else outfile, render_csv(url, m3u8_obj.playlists)
                else:
                    print >> sys.stderr, render_date_iso8601(), "Error for url:", url, "Doesn't contain any stream playlists"
            except IOError as error:
                print >> sys.stderr, render_date_iso8601(), "Error for url:", url, ">>", error
        else:
            print >> sys.stderr, render_date_iso8601(), "Error: Not a valid URL >>", url


    return 0
# enddef main()

# Start program
if __name__ == "__main__":
    main()
