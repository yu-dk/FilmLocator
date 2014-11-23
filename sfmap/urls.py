from django.conf.urls import patterns, url
from sfmap import views

urlpatterns = patterns('',
    ##url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^$', views.index, name='index'),
    url(r'^welcome', views.welcome, name='welcome'),
)