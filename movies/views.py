from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from accounts.models import UserProfile
from .models import Movie, Review, Rating
from django.http import HttpResponseBadRequest



# ------------------------------
# Existing Movie & Review Views
# ------------------------------

def index(request):
    search_term = request.GET.get('search')
    if search_term:
        movies = Movie.objects.filter(name__icontains=search_term)
    else:
        movies = Movie.objects.all()
    
    template_data = {
        'title': 'Movies',
        'movies': movies,
    }
    
    return render(request, 'movies/index.html', {
        'template_data': template_data,
    })


def show(request, id):
    movie = Movie.objects.get(id=id)
    reviews = Review.objects.filter(movie=movie)
    user_rating = None
    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(user=request.user, movie=movie).first()

    template_data = {
        'title': movie.name,
        'movie': movie,
        'reviews': reviews,
        'user_rating': user_rating.value if user_rating else 0,
        'avg_rating': movie.rate_movie(),
    }

    return render(request, 'movies/show.html', {
        'template_data': template_data
    })


@login_required
def create_review(request, id):
    """Allows a logged-in user to create a review for a movie."""
    if request.method == 'POST' and request.POST['comment'] != '':
        movie = Movie.objects.get(id=id)
        review = Review(
            comment=request.POST['comment'],
            movie=movie,
            user=request.user
        )
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)


@login_required
def edit_review(request, id, review_id):
    """Allows users to edit their own reviews."""
    review = get_object_or_404(Review, id=review_id)
    if request.user != review.user:
        return redirect('movies.show', id=id)

    if request.method == 'GET':
        movie = review.movie
        template_data = {
            'title': 'Edit Review',
            'review': review,
            'movie': movie,
            'avg_rating': movie.rate_movie(),
        }
        return render(request, 'movies/edit_review.html', {'template_data': template_data})
    elif request.method == 'POST' and request.POST['comment'] != '':
        review.comment = request.POST['comment']
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)


@login_required
def delete_review(request, id, review_id):
    """Allows users to delete their own reviews."""
    review = get_object_or_404(Review, id=review_id, user=request.user)
    review.delete()
    return redirect('movies.show', id=id)


# ------------------------------
# NEW FEATURE: Trending Movies (based on Purchases)
# ------------------------------

@login_required
def trending_movies(request):
    """
    Display trending movies based on purchase activity from users
    in the same state or country as the current user.
    """
    from cart.models import Item  # use your actual model here!

    user = request.user
    profile = getattr(user, "profile", None)

    # Determine nearby users (by state or country)
    if profile and profile.state:
        nearby_orders = Item.objects.filter(order__state=profile.state)
    elif profile and profile.country:
        nearby_orders = Item.objects.filter(order__country=profile.country)
    else:
        nearby_orders = Item.objects.all()

    # Aggregate trending movies based on item count
    movies = (
        Movie.objects.filter(id__in=nearby_orders.values_list("movie_id", flat=True))
        .annotate(num_purchases=Count("item"))
        .order_by("-num_purchases")[:10]
    )

    template_data = {
        "title": "Trending Movies Near You",
        "movies": movies,
    }

    return render(request, "movies/trending.html", {"template_data": template_data})

@login_required
def rate_movie(request, id):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    movie = get_object_or_404(Movie, pk=id)
    try:
        value = int(request.POST.get("rating", "0"))
    except ValueError:
        return HttpResponseBadRequest("Invalid rating")
    if value < 1 or value > 5:
        return HttpResponseBadRequest("Rating must be 1..5")
    rating, _ = Rating.objects.get_or_create(user=request.user, movie=movie, defaults={"value": value})
    if rating.value != value:
        rating.value = value
        rating.save(update_fields=["value", "updated_at"])
    return redirect("movies.show", id=movie.id)
