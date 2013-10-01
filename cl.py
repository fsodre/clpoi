"""
Usage:
  cl.py <poi_file> <query> [options]
  cl.py -h

 Arguments:
  <poi_file>     Points of Interest file. Ex: poi.txt
  <query>        CIty or area to search. Ex: Sunnyvale

 Options:
  -h --help                  Show this help
  -p --clprefix=<prefix>     craigslist location prefix. [default: sfbay]
  --maxResults=<n>           number of results that must be analyzed to meet your criteria [default: 50]
  --minAsk=<n>               lower bound for rent price [default: 0]
  --maxAsk=<n>               upper bound for rent price [default: 5000]
  -b --bedrooms=<n>          minimum number of bedrooms [default: 1]
  --hasPic=<0|1>             1 to show only entries with pictures [default: 1]
  -r --radius=<r>            maximun distance of the apartments from your points of interest (in kilometers). [default: 0.5]
"""

# This is script fetches results from a search for apartments at craigslist and filters them
# to show results that are close to a given list of points of interest, which are given in an
# external file using the following format:
#
# Point of interest name # 1
# latitude1 longitude1
# Point of interest name # 2
# latitude2 longitude2
# Point of interest name # 3
# latitude3 longitude3
# ...
#
# Author: Felipe Sodre (fsodre@gmail.com)
# License: as is

from docopt import docopt
from math import sin, cos, atan2, sqrt, radians
import re
import time
import urllib
import urllib2

# Distance in kms given two (lat, long) coordinates, using Haversine formula
def distance(c1, c2):
  (lat1, lng1), (lat2, lng2) = c1, c2

  [radLat1, radLng1, radLat2, radLng2] = map(radians, [lat1, lng1, lat2, lng2])

  dlat = radLat2 - radLat1
  dlng = radLng2 - radLng1

  a = sin(dlat/2) * sin(dlat/2) + sin(dlng/2) * sin(dlng/2) * cos(radLat1) * cos(radLat1)
  c = 2 * atan2(sqrt(a), sqrt(1-a))

  return 6371 * c


def mapImage(pivot, entries):
  (plat, plng) = pivot
  markers_str = "markers=color:blue%%7C%f,%f" % (plat, plng)
  for i in xrange(len(entries)):
    ((lat, lng), a, b) = entries[i]
    markers_str += "&markers=color:yellow%%7Clabel:%c%%7C%f,%f" % (chr(ord('A')+i), lat, lng)

  return "http://maps.googleapis.com/maps/api/staticmap?center=%f,%f&zoom=13&size=400x400&%s&sensor=false" % (plat, plng, markers_str)

def pois_from_poi_file(poiFile):
    # Read Points of Interest file
    poislines = []
    with open(poiFile, 'r') as f:
      poislines = [a.strip() for a in f.readlines()]
    return [(poislines[2*i], (float(poislines[2*i+1].split()[0]), float(poislines[2*i+1].split()[1])), []) for i in xrange(len(poislines)/2)]

if __name__ == '__main__':
    params = docopt(__doc__, version='0.1')
    print params

    radius = float(params['--radius'])
    maxResults = float(params['--maxResults'])
    clprefix = params['--clprefix']
    poiFile = params['<poi_file>']

    # Parameters that will be used to search craigslist
    url_params = {
        'minAsk': params['--minAsk'],
        'maxAsk': params['--maxAsk'],
        'bedrooms': params['--bedrooms'],
        'hasPic': params['--hasPic'],
        'query': params['<query>']
    }

    pois = pois_from_poi_file(poiFile)

    # Searches results on craigslis
    count = 0
    pages = 0
    while count < maxResults:
      url = 'http://%s.craigslist.org/search/apa?s=%d&%s' % (clprefix, pages * 100, urllib.urlencode(url_params))
      response = urllib2.urlopen(url)
      html = response.read()

      hasResults = False

      for entry in re.finditer('<p class="row" data-latitude="([^"]+)" data-longitude="([^"]+)".+?href="([^"]+).+?"date">([^<]+).+?html">([^<]+).+?price">([^<]+).+?small>([^<]+)', html, re.DOTALL):
        hasResults = True
        latlng = (float(entry.group(1)), float(entry.group(2)))
        obj = (latlng, entry.group(3), " ".join([entry.group(i) for i in xrange(4,8)]))

        for (name, pos, entries) in pois:
          if distance(latlng, pos) < radius + 1e-100:
            entries.append(obj)

        count += 1

      # Let's not abuse craigslist :)
      time.sleep(1)
      pages += 1

      # Next page is showing no results, finishes the search
      if not hasResults:
        break

    # Output
    print """
    <html>
    <head>
    <style type='text/css'>
    a:link {text-decoration:none; color: blue}
    a:visited {text-decoration:none; color: blue}
    a:hover {text-decoration:none; color: blue; background-color: #c0c0c0}
    a:active {text-decoration:none; color: blue; background-color: #c0c0c0}
    </style>
    </head>
    <body>%d Entries analyzed""" % count

    for (name, pos, entries) in pois:
      if len(entries) == 0: continue
      print "<table style='border:0'><tr><td colspan=2 style='background-color:grey;font-weight:bold'>%d places close to %s:</td></tr>" % (len(entries), name)
      print "<tr><td style='vertical-align: top'><img src=\"%s\"/></td><td style='vertical-align: top; font-weight:bold'>" % mapImage(pos, entries)
      letter = 'A'
      for (latlng, apid, desc) in entries:
        print "%c: <a href=\"http://%s.craigslist.org%s\">[%.4f km] %s</a><br/>" % (letter, clprefix, apid, distance(latlng, pos), desc)
        letter = chr(ord(letter)+1)
      print "</td></tr></table><hr/>"

    print "</body></html>"

