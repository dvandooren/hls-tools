#!/usr/bin/env python
# Return Codes - Sensu compatible
# 0: ok
# 1: warning
# 2: critical
# 3 or more: unknown

# TODO: Add unordered check
# TODO: Add a variance for the bandwidth numbers as a percentage

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

    parser.add_argument('-b', '--bandwidths',
                        action='store',
                        required=True,
                        help='Quoted list of bandwidths to check profile against. ie. "889000 3767000 741000 4504000 1347000 2531000 2294000 1873000"')

    parser.add_argument('-p', '--variance-percent',
                        action='store',
                        type=float,
                        help='For dynamically created bandwidths, define a percentage as a float for +/- variance of listed expected bandwidths')

    parser.add_argument('-u', '--unordered',
                        action='store_true',
                        default=False,
                        help="Just validate the bandwidth is defined, don't validate the order")

    parser.add_argument('-f', '--file',
                        action='store',
                        help='File of URLs to load. This overrides a URL provided on the command-line')

    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        default=False,
                        help='Display verbose output')

    parser.add_argument('-t', '--timestamp',
                        action='store_true',
                        default=False,
                        help='Display timestamp in the brief output')

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

def print_brief(timestamp, out_stream, *items):
    output = ' '.join(map(str, items))
    if timestamp:
        print >> out_stream, render_date_iso8601(), output
    else:
        print >> out_stream, output
# endef print_brief()

# This function sets the return code only if the new code is worse
def set_return_code(return_code, new_code):
    return new_code if return_code < new_code else return_code
# enddef set_return_code

def get_bandwidths(playlists):
    bandwidths = []
    for playlist in playlists:
        bandwidths.append(str(playlist.stream_info.bandwidth))

    return bandwidths
# enddef get_bandwidths()

def check_ordered_bandwidths(playlists, ref_bandwidths, verbose):
    return_code = 0
    error_msg = ""

    play_bandwidths = get_bandwidths(playlists)

    if len(ref_bandwidths) > len(play_bandwidths):
        return_code = set_return_code(return_code, 2)     # Critical since we must at least have the required bandwidths
        error_msg += "Missing bandwidths,"

    if len(ref_bandwidths) < len(play_bandwidths):
        return_code = set_return_code(return_code, 1)     # Warning since we are not expecting more than the required bandwidths
        error_msg += "Additional bandwidths,"

    out_of_order_flag = False
    missing_flag = False
    for idx, bandwidth in enumerate(ref_bandwidths):
        try:
            if play_bandwidths.index(bandwidth) != idx:
                if not out_of_order_flag:
                    return_code = set_return_code(return_code, 1)   # Warning since we have the bandwidth but it's just not in the correct order
                    error_msg += "Incorrect bandwidth order,"
                    out_of_order_flag = True

                if verbose:
                    print >> sys.stdout, "\tIncorrect order for bandwidth", bandwidth, "expected index:", idx, "got index:", play_bandwidths.index(bandwidth)
            else:
                if verbose:
                    print >> sys.stdout, "\tFound bandwidth", bandwidth, "at the correct index", idx
        except ValueError:
            if not missing_flag:
                return_code = set_return_code(return_code, 2)   # Critical since we are missing this bandwidth
                error_msg += "Missing bandwidths,"
                missing_flag = True

            if verbose:
                print >> sys.stdout, "\tMissing bandwidth", bandwidth


    return (return_code, error_msg)
# enddef check_ordered_bandwidths()

def check_unordered_bandwidths(playlists, ref_bandwidths, verbose):
    return_code = 0
    error_msg = ""

    play_bandwidths = get_bandwidths(playlists)

    if len(ref_bandwidths) > len(play_bandwidths):
        return_code = set_return_code(return_code, 2)     # Critical since we must at least have the required bandwidths
        error_msg += "Missing bandwidths,"

    if len(ref_bandwidths) < len(play_bandwidths):
        return_code = set_return_code(return_code, 1)     # Warning since we are not expecting more than the required bandwidths
        error_msg += "Additional bandwidths,"

    for idx, bandwidth in enumerate(ref_bandwidths):
        missing_flag = False

        try:
            # This will throw an exception if the bandwidth is not in the play_bandwidths list
            play_bandwidths.index(bandwidth)

            if verbose:
                print >> sys.stdout, "\tFound bandwidth", bandwidth

        except ValueError:
            if not missing_flag:
                return_code = set_return_code(return_code, 2)   # Critical since we are missing this bandwidth
                error_msg += "Missing bandwidths,"
                missing_flag = True

            if verbose:
                print >> sys.stdout, "\tMissing bandwidth", bandwidth


    return (return_code, error_msg)
# endef check_unordered_bandwidths()

def find_variance_bandwidth_index(min_bandwidths, max_bandwidths, play_bandwidth):
    found_index = -1
    for idx in range(len(min_bandwidths)):
        if (int(play_bandwidth) <= int(max_bandwidths[idx])) and (int(play_bandwidth) >= int(min_bandwidths[idx])):
            found_index = idx

    return found_index
# enddef find_variance_bandwidth_index()

def check_variance_bandwidths(playlists, ref_bandwidths, variance, verbose, unordered):
    return_code = 0
    error_msg = ""

    min_bandwidths = get_min_bandwidths(ref_bandwidths, variance)
    max_bandwidths = get_max_bandwidths(ref_bandwidths, variance)
    play_bandwidths = get_bandwidths(playlists)

    if len(ref_bandwidths) > len(play_bandwidths):
        return_code = set_return_code(return_code, 2)     # Critical since we must at least have the required bandwidths
        error_msg += "Missing bandwidths,"

    if len(ref_bandwidths) < len(play_bandwidths):
        return_code = set_return_code(return_code, 1)     # Warning since we are not expecting more than the required bandwidths
        error_msg += "Additional bandwidths,"

    for idx, play_bandwidth in enumerate(play_bandwidths):
        bandwidth = int(play_bandwidth)
        found_idx = find_variance_bandwidth_index(min_bandwidths,max_bandwidths, play_bandwidth)
        if found_idx == -1:
            if len(ref_bandwidths) == len(play_bandwidths):
                return_code = set_return_code(return_code, 2)   # Critical since we have a bandwidth that's not expected
                error_msg += "Mismatched bandwidths,"
            else:
                return_code = set_return_code(return_code, 1)   # Warning since we have an extra bandwidth
                error_msg += "Additional bandwidths,"

            if verbose:
                print "\tBandwidth:", bandwidth, "is not expected"
        else:
            if found_idx == idx or (found_idx >= 0 and unordered):
                if verbose:
                    print >> sys.stdout, "\tBandwidth", bandwidth, "within variance of", ref_bandwidths[found_idx]
            else:
                return_code = set_return_code(return_code, 1)   # Warning since we have the bandwidth but it's just not in the correct order
                error_msg += "Incorrect bandwidth order,"
                if verbose:
                    print >> sys.stdout, "\tIncorrect order for bandwidth", play_bandwidth, "expected index:", idx, "got index:", found_idx


    return (return_code, error_msg)
# enddef check_variance_bandwidths()

def get_min_bandwidths(ref_bandwidths, variance):
    min_bandwidths = []
    for bandwidth in ref_bandwidths:
        min_bandwidth = 0
        try:
            min_bandwidth = int(int(bandwidth) - (int(bandwidth) * (variance / 100)))
            min_bandwidths.append(min_bandwidth)

        except ValueError:
            print >> sys.stdout, "CRITICAL: Invaid bandwidth value:", bandwidth, "is not an integer"
            exit(2)

    return min_bandwidths

# endef get_min_bandwidths()

def get_max_bandwidths(ref_bandwidths, variance):
    max_bandwidths = []
    for bandwidth in ref_bandwidths:
        max_bandwidth = 0
        try:
            max_bandwidth = int(int(bandwidth) + (int(bandwidth) * (variance / 100)))
            max_bandwidths.append(max_bandwidth)

        except ValueError:
            print >> sys.stdout, "CRITICAL: Invaid bandwidth value:", bandwidth, "is not an integer"
            exit(2)

    return max_bandwidths

# endef get_max_bandwidths()


def main():
    """
    Simple command-line program for checking the stream bandwidths to ensure they are what is expected.
    """
    args = get_args()

    if args.verbose:
        args.timestamp = True

    ref_bandwidths = args.bandwidths.split()
    urls = get_urls(args)
    result = (0, "OK")
    result_code = 0

    if len(urls) < 1:
        print >> sys.stderr, render_date_iso8601(), "No valid URLs to process."
        exit(2)

    for url in urls:
        if verify_url(url) == True:
            try:
                m3u8_obj = m3u8.load(url)
                if m3u8_obj.is_variant:
                    if args.verbose:
                        print >> sys.stdout, "Checking URL:", url

                    if args.variance_percent:
                        result = check_variance_bandwidths(m3u8_obj.playlists, ref_bandwidths, args.variance_percent, args.verbose, args.unordered)
                    else:
                        if args.unordered:
                            result = check_unordered_bandwidths(m3u8_obj.playlists, ref_bandwidths, args.verbose)
                        else:
                            result = check_ordered_bandwidths(m3u8_obj.playlists, ref_bandwidths, args.verbose)

                    result_code = set_return_code(result_code, result[0])

                    if result[0] == 0:
                        print_brief(args.timestamp, sys.stdout, "OK: URL=", url)
                    elif result[0] == 1:
                        print_brief(args.timestamp, sys.stdout, "WARNING: URL=", url, ">>", result[1][:-1])
                    else:
                        print_brief(args.timestamp, sys.stdout, "CRITICAL: URL=", url, ">>", result[1][:-1])


                else:
                    print_brief(args.timestamp, sys.stdout, "CRITICAL: URL=", url, ">> Does not contain any variant playlists")
                    result_code = 2
            except IOError as error:
                print_brief(args.timestamp, sys.stdout, "CRITICAL: URL=", url, ">>", error)
                result_code = 2
        else:
            print_brief(args.timestamp, sys.stdout, "CRITICAL: URL=", url, ">> Not a valid URL")
            result_code = 2

    if result_code != 0:
        exit(result_code)

    return 0
# enddef main()

# Start program
if __name__ == "__main__":
    main()
