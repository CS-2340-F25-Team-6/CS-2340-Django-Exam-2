from django.contrib import admin

# Register your models here.
from .models import Movie, Review, Rating
admin.site.register(Movie)
admin.site.register(Review)
admin.site.register(Rating)
