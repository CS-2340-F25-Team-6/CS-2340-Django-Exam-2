from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponseBadRequest
from .models import Movie, Review, Rating
from accounts.models import UserProfile
from cart.models import Item, Order  # ✅ needed for region-based filtering
from django.db.models import Sum


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
# UPDATED FEATURE: Trending Movies
# ------------------------------

@login_required
def trending_movies(request):
    user = request.user
    profile = getattr(user, "profile", None)

    state_param = request.GET.get("state")

    if state_param:
        filter_state = state_param
        title = f"🎬 Trending Movies in {state_param}"
    elif profile and profile.state:
        filter_state = profile.state
        title = "🎬 Trending Movies Near You"
    elif profile and profile.country:
        orders = Order.objects.filter(country=profile.country)
        movie_counts = {}
        for order in orders:
            items = Item.objects.filter(order=order).select_related('movie')
            for item in items:
                movie = item.movie
                if movie not in movie_counts:
                    movie_counts[movie] = 0
                movie_counts[movie] += item.quantity
        
        sorted_movies = sorted(movie_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        movies = [movie for movie, count in sorted_movies]
        for movie in movies:
            movie.purchase_count = movie_counts[movie]
        
        template_data = {
            "title": "🎬 Trending Movies in Your Country",
            "movies": movies,
        }
        return render(request, "movies/trending.html", {"template_data": template_data})
    else:
        filter_state = None
        title = "🎬 Trending Movies Overall"

    if filter_state:
        orders = Order.objects.filter(state=filter_state)
    else:
        orders = Order.objects.all()
    
    movie_counts = {}
    for order in orders:
        items = Item.objects.filter(order=order).select_related('movie')
        for item in items:
            movie = item.movie
            if movie not in movie_counts:
                movie_counts[movie] = 0
            movie_counts[movie] += item.quantity
    
    sorted_movies = sorted(movie_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    movies = [movie for movie, count in sorted_movies]
    for movie in movies:
        movie.purchase_count = movie_counts[movie]

    template_data = {
        "title": title,
        "movies": movies,
    }

    return render(request, "movies/trending.html", {"template_data": template_data})

    # ✅ Aggregate trending movies (based on item count)
    if filter_state:
        movies = (
            Movie.objects.filter(item__order__state=filter_state)
            .annotate(
                purchase_count=Sum('item__quantity'),
                num_reviews=Count("review")
            )
            .order_by("-purchase_count")[:10]
        )
    else:
        movies = (
            Movie.objects.filter(item__isnull=False)
            .annotate(
                purchase_count=Sum('item__quantity'),
                num_reviews=Count("review")
            )
            .order_by("-purchase_count")[:10]
        )

    template_data = {
        "title": title,
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
