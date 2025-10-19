from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Movie(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    price = models.IntegerField()
    description = models.TextField()
    image = models.ImageField(upload_to='movie_images/')

    def __str__(self):
        return str(self.id) + ' - ' + self.name
    
    def rate_movie(self):
        reviews_with_ratings = self.review_set.filter(rating__gt=0)
        if reviews_with_ratings.exists():
            total_rating = sum(review.rating for review in reviews_with_ratings)
            return round(total_rating / reviews_with_ratings.count(), 1)
        return 0.0
    
class Review(models.Model):
    id = models.AutoField(primary_key=True)
    comment = models.CharField(max_length=255)
    rating = models.IntegerField(default=0, choices=[(i, i) for i in range(1, 6)])
    date = models.DateTimeField(auto_now_add=True)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id) + ' - ' + self.movie.name
