from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    #url(r'^$', 'SF_film.views.home', name='home'),
    #url(r'^admin/', include(admin.site.urls)),
    url(r'^sfmap/', include('sfmap.urls', namespace="sfmap")),
)
