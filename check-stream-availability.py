#!/usr/bin/env python
# Return Codes - Sensu compatible
# 0: ok
# 1: warning
# 2: critical
# 3 or more: unknown

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
        description='Check profile bitrates match provided list')

    parser.add_argument('-f', '--file',
                        action='store',
                        help='File of URLs to load. This overrides a URL provided on the command-line')

    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        default=False,
                        help='Display verbose output')

    parser.add_argument('url',
                        nargs='?', default='NO_URL',
                        action='store',
                        help='The url of the m3u8 file')



    args = parser.parse_args()
    if args.url == "NO_URL" and not args.file:
        print >> sys.stderr, "Error: You must either specify a URL on the command-line or provide a filename via the --file argument\n\n"
        parser.print_help()
        exit(2)

    return args
# enddef get_args()

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

def render_date_iso8601():
    timestamp = time.strftime('%Y-%m-%dT%H:%M:%S%z', time.localtime())
    return timestamp
# enddef render_date_iso8601()

# This function sets the return code only if the new code is worse
def set_return_code(return_code, new_code):
    return new_code if return_code < new_code else return_code
# enddef set_return_code

def check_streams(variant_streams, base_uri, verbose):
    result_msg = "BaseURI="
    result_msg += base_uri
    result_msg += " >> "
    result_code = 0

    for stream in variant_streams:
        result = ""
        stream_url = ""
        stream_url = base_uri
        stream_url += stream.uri

        try:
            stream_playlist = m3u8.load(stream_url)
            result = "OK"
            result_msg += stream.uri
            result_msg += ":"
            result_msg += result
            result_msg += ", "
        except IOError as error:
            result =  str(error)
            result_code = 2
            result_msg += stream.uri
            result_msg += ":"
            result_msg += result
            result_msg += ", "

        # print stream_url
        if verbose:
            print "\t%s: %s" % (stream.uri, result)

    return (result_code, result_msg[:-2])

# enddef check_streams()

def main():
    """
    Simple command-line program for checking the availability of streams within a master m3u8 playlist.
    """
    args = get_args()

    urls = get_urls(args)
    result = (0, "OK")
    result_code = 0

    if len(urls) < 1:
        print >> sys.stderr, render_date_iso8601(), "No valid URLs to process."
        exit(2)

    for url in urls:
        if verify_url(url) == True:
            try:
                master_playlist = m3u8.load(url)
                if master_playlist.is_variant:
                    if args.verbose:
                        print >> sys.stdout, render_date_iso8601(), "Checking URL:", url

                    result = check_streams(master_playlist.playlists, master_playlist.base_uri, args.verbose)
                    result_code = set_return_code(result_code, result[0])

                    if not args.verbose:
                        if result[0] == 0:
                            print >> sys.stdout, "OK:", result[1]
                        elif result[0] == 1:
                            print >> sys.stdout, "WARNING:", result[1]
                        else:
                            print >> sys.stdout, "CRITICAL:", result[1]

                else:
                    if args.verbose:
                        print >> sys.stdout, render_date_iso8601(), "CRITICAL: URL=", url, ">> Does not contain any streams"
                    else:
                        print >> sys.stdout, "CRITICAL: URL=", url, ">> Does not contain any streams"
                    result_code = 2
            except IOError as error:
                if args.verbose:
                    print >> sys.stdout, render_date_iso8601(), "CRITICAL: URL=", url, ">>", error
                else:
                    print >> sys.stdout, "CRITICAL: URL=", url, ">>", error
                result_code = 2
        else:
            if args.verbose:
                print >> sys.stdout, render_date_iso8601(), "CRITICAL: URL=", url, ">> Not a valid URL"
            else:
                print >> sys.stdout, "CRITICAL: URL=", url, ">> Not a valid URL"
            result_code = 2

    if result_code != 0:
        exit(result_code)

    return 0
# enddef main()

# Start program
if __name__ == "__main__":
    main()
