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
# Usage: python cl.py clprefix=[s] maxResults=[n] minAsk=[n] maxAsk=[n] bedrooms=[n] hasPic=[0-1] query=[s] radius=[f], poi=[s]
# 
# clprefix: craigslist location prefix. Ex: sfbay
# maxResults: number of results that must be analyzed to meet your criteria
# minAsk: lower bound for rent price
# maxAsk: upper bound for rent price
# bedrooms: minimun amount of rooms
# hasPic: 1 to show only entries with pictures
# query: search query (usually the name of the city/neighborhood). Can be an empty string.; Ex: "Mountain View"
# radius: maximun distance of the apartments from your points of interest (in kilometers). Ex: 0.5
# poi: Points of Interest file. Ex: poi.txt
# 
# Author: Felipe Sodre (fsodre@gmail.com)
# License: as is

import urllib2
import re
import time
import sys
import urllib
from math import sin, cos, atan2, sqrt, radians


# Distance in kms given two (lat, long) coordinates, using Haversine formula
def distance(c1, c2):
  (lat1, lng1), (lat2, lng2) = c1, c2

  [radLat1, radLng1, radLat2, radLng2] = map(radians, [lat1, lng1, lat2, lng2])

  dlat = radLat2 - radLat1
  dlng = radLng2 - radLng1

  a = sin(dlat/2) * sin(dlat/2) + sin(dlng/2) * sin(dlng/2) * cos(radLat1) * cos(radLat1)
  c = 2 * atan2(sqrt(a), sqrt(1-a))

  return 6371 * c


params = dict([(arg.split('=')[0], arg.split('=')[1]) for arg in sys.argv if '=' in arg])

if any([key not in params for key in ['clprefix', 'maxResults', 'minAsk', 'maxAsk', 'bedrooms', 'hasPic', 'query', 'radius', 'poi']]):
  print 'Syntax: %s clprefix=[s] maxResults=[n] minAsk=[n] maxAsk=[n] bedrooms=[n] hasPic=[0-1] query=[s] radius=[f], poi=[s]' % sys.argv[0]
  print 'clprefix: craigslist location prefix. Ex: sfbay'
  print 'maxResults: number of results that must be analyzed to meet your criteria'
  print 'minAsk: lower bound for rent price'
  print 'maxAsk: upper bound for rent price'
  print 'bedrooms: minimun amount of rooms'
  print 'hasPic: 1 to show only entries with pictures'
  print 'query: search query (usually the name of the city/neighborhood). Can be an empty string; Ex: "Mountain View"'
  print 'radius: maximun distance of the apartments from your points of interest (in kilometers). Ex: 0.5'
  print 'poi: Points of Interest file. Ex: poi.txt'
  sys.exit()

radius = float(params['radius'])
maxResults = float(params['maxResults'])
clprefix = params['clprefix']
poiFile = params['poi']

for key in ['radius', 'maxResults', 'clprefix', 'poi']:
  del params[key]

# Read Points of Interest file
poislines = []
with open(poiFile, 'r') as f:
  poislines = [a.strip() for a in f.readlines()]

pois = [(poislines[2*i], (float(poislines[2*i+1].split()[0]), float(poislines[2*i+1].split()[1])), []) for i in xrange(len(poislines)/2)]

# Searches results on craigslis
count = 0
pages = 0

while count < maxResults:
  url = 'http://%s.craigslist.org/search/apa?s=%d&%s' % (clprefix, pages * 100, urllib.urlencode(params))
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

def mapImage(pivot, entries):
  (plat, plng) = pivot
  markers_str = "markers=color:blue%%7C%f,%f" % (plat, plng)
  for i in xrange(len(entries)):
    ((lat, lng), a, b) = entries[i]
    markers_str += "&markers=color:yellow%%7Clabel:%c%%7C%f,%f" % (chr(ord('A')+i), lat, lng)

  return "http://maps.googleapis.com/maps/api/staticmap?center=%f,%f&zoom=13&size=400x400&%s&sensor=false" % (plat, plng, markers_str)

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

