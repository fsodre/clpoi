clpoi
===

This is script fetches results from a search for apartments at craigslist and filters them
to show results that are close to a given list of points of interest.

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


Format for the points of interest file:

    Point of interest name # 1
    latitude1 longitude1
    Point of interest name # 2
    latitude2 longitude2
    Point of interest name # 3
    latitude3 longitude3
    ...

