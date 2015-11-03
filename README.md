# HLS Tools

These are just a few python scripts hacked together to help diagnose/check HLS streams.

> **Requirements:**
> There's only 2 external requirements to run this script, and they can both be installed by running `pip install -r requirements.txt`

The **check** scripts can be run in verbose mode `(-v or --verbose)` or in *brief* mode which returns the output usable as a Sensu check.

All the scripts can be run by specifying a URL on the command-line or by using the file mode `(-f or --file)` to provide a list of URLs (one per line).

### check-stream-availability.py
This script checks to ensure all the stream m3u8 playlists listed in the master playlist are available (ie. downloadable).

##### Example of running in verbose mode
```bash
$ ./check-stream-availability.py -v -f test.urls
2015-11-03T09:40:57-0500 Checking URL: https://devimages.apple.com.edgekey.net/streaming/examples/bipbop_4x3/bipbop_4x3_variant.m3u8
        gear1/prog_index.m3u8: OK
        gear2/prog_index.m3u8: OK
        gear3/prog_index.m3u8: OK
        gear4/prog_index.m3u8: OK
        gear0/prog_index.m3u8: OK
2015-11-03T09:40:59-0500 Checking URL: https://devimages.apple.com.edgekey.net/streaming/examples/bipbop_16x9/bipbop_16x9_variant.m3u8
        gear1/prog_index.m3u8: OK
        gear2/prog_index.m3u8: OK
        gear3/prog_index.m3u8: OK
        gear4/prog_index.m3u8: OK
        gear5/prog_index.m3u8: OK
        gear0/prog_index.m3u8: OK
2015-11-03T09:41:02-0500 Checking URL: http://localhost:8000/missing.m3u8
        gear1/prog_index.m3u8: OK
        gear2/prog_index.m3u8: OK
        gear3/prog_index.m3u8: HTTP Error 404: File not found
        gear4/prog_index.m3u8: OK
        gear0/prog_index.m3u8: OK
```        
##### Example of running in brief mode
```bash
$ ./check-stream-availability.py  -f test.urls  
OK: BaseURI=https://devimages.apple.com.edgekey.net/streaming/examples/bipbop_4x3/ >> gear1/prog_index.m3u8:OK, gear2/prog_index.m3u8:OK, gear3/prog_index.m3u8:OK, gear4/prog_index.m3u8:OK, gear0/prog_index.m3u8:OK
OK: BaseURI=https://devimages.apple.com.edgekey.net/streaming/examples/bipbop_16x9/ >> gear1/prog_index.m3u8:OK, gear2/prog_index.m3u8:OK, gear3/prog_index.m3u8:OK, gear4/prog_index.m3u8:OK, gear5/prog_index.m3u8:OK, gear0/prog_index.m3u8:OK
CRITICAL: BaseURI=http://localhost:8000/ >> gear1/prog_index.m3u8:OK, gear2/prog_index.m3u8:OK, gear3/prog_index.m3u8:HTTP Error 404: File not found, gear4/prog_index.m3u8:OK, gear0/prog_index.m3u8:OK
```

---

### list-stream-profiles.py
This script downloads the master m3u8 playlist file and creates a CSV file with the bandwidth and resolutions. It can either run for a single playlist or a group of playlist by specifying the `--file` option and provided a list of URLs in the file.
```
$ ./list-stream-profiles.py https://devimages.apple.com.edgekey.net/streaming/examples/bipbop_4x3/bipbop_4x3_variant.m3u8
```

-or-

```
$ ./list-stream-profiles.py --file sample.urls
```

By default it will dump the CSV to the stdout, but you can specify a file with the `--output` option. This will create/overwrite the output file provided. If you wish to append to the file use the `--append` option
```
$ ./list-stream-profiles.py --file sample.urls --output sample.csv --append
```

---

#### Running a local test server
The `test_server` directory has a `missing.m3u8` playlist that can be used to test the scripts. You can run a simple HTTP server running on port 8000 using the following commands:
```bash
$ cd test_server
$ python -m SimpleHTTPServer
```
