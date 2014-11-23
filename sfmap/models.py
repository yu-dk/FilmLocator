from django.db import models

# Create your models here.
class Film(models.Model):
    film_name = models.CharField(max_length=250)
    release_year = models.IntegerField('release_year', default=0)

    def __str__(self):
        return self.film_name

    class Meta:
        ordering = ('film_name',)

class Location(models.Model):
    film = models.ManyToManyField(Film)
    location_name = models.CharField(max_length=250)
    geo_lat = models.FloatField('latitude')
    geo_lng = models.FloatField('longitude')
    radius = models.IntegerField(default=-1)

    def __str__(self):
        return self.location_name

