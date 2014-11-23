"""
convert addr to geographic coordinates, and save it in the DB
"""

from django.core.management.base import BaseCommand, CommandError
from django.db.transaction import commit_on_success
import sys, os, simplejson, urllib, pickle
from urllib.error import URLError, HTTPError
from SF_film.settings import FILM_API_URL, GOOGLE_GEO_URL, SEARCH_CITY, SERVER_KEY, MAX_DIST, TEMP_DBSTORE
from sfmap.models import Film, Location

def _addr_format(x):
    x = x.strip()
    if not x:
        return x
    if x[-1] in [',', '.']:
        return x[:-1]
    else:
        return x

def get_url_response(base_url, params):
    #print(base_url + urllib.parse.urlencode(params))
    try:
        response = urllib.request.urlopen(base_url + urllib.parse.urlencode(params))
        return response
    except HTTPError as e:
        print('The server could not fulfill the request.')
        print('Error code: ', e.code)
        return None
    except URLError as e:
        print('We failed to reach a server.')
        print('Reason: ', e.reason)
        return None

@commit_on_success
def get_film_info():
    """fetch film info online using its API defined in settings.py, store temp data in TEMP_DBSTORE file"""
    if not os.path.exists(TEMP_DBSTORE) or not os.stat(TEMP_DBSTORE).st_size:
        print(TEMP_DBSTORE, 'is empty, fetching data and writing ...')
        params = {'$select': 'title, locations, release_year'}
        response = get_url_response(FILM_API_URL, params)
        if response is None:
            sys.exit(0)
        result = simplejson.load(response)
        pickle.dump(result, open(TEMP_DBSTORE, 'wb'))
    else:
        result = pickle.load(open(TEMP_DBSTORE, 'rb'))

    for rec in result:
        try:
            title = rec['title']
            location = rec['locations']
        except:
            continue
        release_year = rec.get('release_year', 0)
        f, _ = Film.objects.get_or_create(film_name=title, release_year=release_year)
        location = _addr_format(location)
        l, _ = Location.objects.get_or_create(location_name=location, geo_lat = 0, geo_lng = 0)
        l.film.add(f)

def getDistTwoPoints(pa, pb):
    from math import sin, cos, radians, degrees, acos
    lat_a = radians(pa['lat'])
    lat_b = radians(pb['lat'])
    long_diff = radians(pa['lng'] - pb['lng'])
    distance = (sin(lat_a) * sin(lat_b) +
                cos(lat_a) * cos(lat_b) * cos(long_diff))
    resToMile = degrees(acos(distance)) * 69.09
    resToMt = resToMile / 0.00062137119223733
    return resToMt

def check_locality_border(r):
    assert ('address_components' in r)
    flag = 0
    for components in r['address_components']:
        if SEARCH_CITY.upper() in components['long_name'].upper():
            flag = 1
            break
    if not flag:
            return -1

    if 'bounds' not in r['geometry']:
        return 0
    point1 = r['geometry']['bounds']['northeast']
    point2 = r['geometry']['bounds']['southwest']
    return getDistTwoPoints(point1, point2)

def parse_geo_result(result):
    lats, lngs, rs = [], [], []
    for r in result['results']:
        radius = check_locality_border(r)
        #print(radius,'radius')
        if radius >= 0 and radius <= MAX_DIST:
            lats.append(r['geometry']['location']['lat'])
            lngs.append(r['geometry']['location']['lng'])
            rs.append(radius)

    if not lats:
        return None

    return {'lat': sum(lats)/len(lats),
            'lng': sum(lngs)/len(lngs),
            'radius': min(rs)}

def get_geo_data():
    for l in Location.objects.all():
        params = {'address': l.location_name + ',' + SEARCH_CITY,
            'region': 'en',
            'key': SERVER_KEY,
            'sensor': 'false'}
        response = get_url_response(GOOGLE_GEO_URL, params)
        if response is None:
            continue
        result = simplejson.load(response)
        if result['status'] != 'OK' or len(result.get('results', [])) not in [1, 2]:
            continue
        geo = parse_geo_result(result)
        if geo is not None:
            l.geo_lat = geo['lat']
            l.geo_lng = geo['lng']
            l.radius = geo['radius']
            l.save()

def _debug_geo_failed():
    """print out address that failed to get a precious geocode (within 2000m resolution) using Google API"""
    n = 0
    for l in Location.objects.all():
        if (l.radius == -1):
            print(l.location_name)
            n += 1
    print(n, 'out of', len(Location.objects.all()), 'locations without geocoding within 2000m resolution')

class Command(BaseCommand):
    def handle(self, *args, **options):
        get_film_info()
        get_geo_data()
        ##_debug_geo_failed()
