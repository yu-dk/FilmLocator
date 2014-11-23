from django.test import TestCase
from sfmap.management.commands.import_data import get_url_response, parse_geo_result
from SF_film.settings import SERVER_KEY, GOOGLE_GEO_URL
import simplejson

class GeocodingTestCase(TestCase):
    def setUp(self):
        self.addr = 'City Hall, San Francisco'

    def test_http_response(self):
        params = {'address': self.addr,
                'region': 'en',
                'key': SERVER_KEY,
                'sensor': 'false'}

        response = get_url_response(GOOGLE_GEO_URL, params)
        self.assertIsNotNone(response, "response using Google GEO API is None")
        result = simplejson.load(response)
        self.assertEqual(result['status'], 'OK')
        geo_info = parse_geo_result(result)
        ###  Google Maps APIs Geocoders provide different locations than Google Maps
        ###  https://developers.google.com/maps/faq#geocoder_differences
        self.assertIsNone(geo_info)


