from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from .models import Movie, Review
from accounts.models import UserProfile
from cart.models import Item  # ✅ needed for region-based filtering


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

    template_data = {
        'title': movie.name,
        'movie': movie,
        'reviews': reviews,
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
        template_data = {
            'title': 'Edit Review',
            'review': review,
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
    """
    Display trending movies based on review activity or purchase data.
    Now supports filtering by ?state= parameter for integration with
    the popularity map feature.
    """
    user = request.user
    profile = getattr(user, "profile", None)

    # ✅ Check for ?state= parameter in URL
    state_param = request.GET.get("state")

    # Determine nearby users/orders based on state or country
    if state_param:
        nearby_orders = Item.objects.filter(order__state=state_param)
        title = f"🎬 Trending Movies in {state_param}"
    elif profile and profile.state:
        nearby_orders = Item.objects.filter(order__state=profile.state)
        title = "🎬 Trending Movies Near You"
    elif profile and profile.country:
        nearby_orders = Item.objects.filter(order__country=profile.country)
        title = "🎬 Trending Movies in Your Country"
    else:
        nearby_orders = Item.objects.all()
        title = "🎬 Trending Movies Overall"

    # ✅ Aggregate trending movies (based on item count)
    movies = (
        Movie.objects.filter(item__in=nearby_orders)
        .annotate(num_reviews=Count("review"))
        .order_by("-num_reviews")[:10]
    )

    template_data = {
        "title": title,
        "movies": movies,
    }

    return render(request, "movies/trending.html", {"template_data": template_data})
