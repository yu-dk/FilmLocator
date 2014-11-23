from django.shortcuts import render, get_object_or_404
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core import serializers
from django import forms
from django.views.decorators.csrf import csrf_exempt
import re,json
from sfmap.models import Film, Location
from SF_film.settings import SERVER_KEY, CITY_LAT, CITY_LNG

# Create your views here.

def match_name(prefix, names):
    matches = []
    for name in names:
        if re.search(r'^'+prefix, name, re.IGNORECASE):
            matches.append(name)
    return matches

def welcome(request):
    film_name = request.GET.get('film_name')
    context = {'film_name': film_name, 'SERVER_KEY': SERVER_KEY, 'center_lat': CITY_LAT, 'center_lng': CITY_LNG}
    if not film_name:
        return HttpResponseRedirect(reverse('sfmap:index'))

    locs = Location.objects.filter(film__film_name = film_name)
    if not locs:
        raise Http404

    ##addr_not_located = [l.location_name for l in locs if l.radius == -1]
    locs = locs.exclude(radius__exact = -1)
    context['locs'] = locs
    context['addr_located'] = [l.location_name for l in locs]
    context['locs_js'] = serializers.serialize('json', locs)
    if len(locs):
        latlng = [(l.geo_lat, l.geo_lng) for l in locs]
        context['center_lat'] = sum([i[0] for i in latlng]) / len(locs)
        context['center_lng'] = sum([i[1] for i in latlng]) / len(locs)
    return render(request, 'sfmap/welcome.html', context)

class FilmNameForm(forms.Form):
    film_name = forms.CharField(label='', max_length=100)


@csrf_exempt
def index(request):
    film_names = list(set([d.film_name for d in Film.objects.all()]))
    if request.method == 'POST':
        form = FilmNameForm(request.POST)
        if form.is_valid():
            name_prefix = form.cleaned_data['film_name']
            matches = match_name(name_prefix, film_names)
            print(matches)
            return HttpResponse(json.dumps(matches), content_type='application/json')
    else:
        form = FilmNameForm()
        film_example = film_names[:min(len(film_names), 5)]
        return render(request, 'sfmap/index.html', {'form': form, 'film_example': film_example})


