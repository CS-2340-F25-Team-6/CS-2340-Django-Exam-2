from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpRequest
from cart.models import Item, Order
from movies.models import Movie
from .utils import calculate_cart_total
from django.contrib.auth.decorators import login_required
from accounts.forms import LocationForm

# Create your views here.

def index(request):
    cart_total = 0
    movies_in_cart = []
    cart = request.session.get('cart', {})
    movie_ids = list(cart.keys())
    if (movie_ids != []):
        movies_in_cart = Movie.objects.filter(id__in=movie_ids)
        cart_total = calculate_cart_total(
            cart,
            movies_in_cart
        )

    template_data = {}
    template_data['title'] = 'Cart'
    template_data['movies_in_cart'] = movies_in_cart
    template_data['cart_total'] = cart_total

    return render(request, 'cart/index.html', {
       'template_data': template_data
    })

def add(request: HttpRequest, id: int):
    get_object_or_404(Movie, id=id)
    cart = request.session.get('cart', {})
    cart[id] = request.POST['quantity']
    request.session['cart'] = cart
    return redirect('cart.index')

def clear(request):
    request.session['cart'] = {}
    return redirect('cart.index')

@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    movie_ids = list(cart.keys())

    if (movie_ids == []):
        return redirect('cart.index')
    
    movies_in_cart = Movie.objects.filter(id__in=movie_ids)
    cart_total = calculate_cart_total(cart, movies_in_cart)

    if request.method == 'GET':
        # Pre-populate form with user's profile data if available
        initial_data = {}
        if hasattr(request.user, 'profile') and request.user.profile:
            initial_data = {
                'state': request.user.profile.state,
                'country': request.user.profile.country
            }
        
        location_form = LocationForm(initial=initial_data)
        
        template_data = {}
        template_data['title'] = 'Checkout'
        template_data['movies_in_cart'] = movies_in_cart
        template_data['cart_total'] = cart_total
        template_data['location_form'] = location_form

        return render(request, 'cart/checkout.html', {'template_data': template_data})
    
    elif request.method == 'POST':
        location_form = LocationForm(request.POST)
        if location_form.is_valid():
            # Save location to user profile
            if hasattr(request.user, 'profile'):
                request.user.profile.state = location_form.cleaned_data['state']
                request.user.profile.country = location_form.cleaned_data['country']
                request.user.profile.save()
            
            # Create order with location information
            order = Order()
            order.user = request.user
            order.total = cart_total
            order.state = location_form.cleaned_data['state']
            order.country = location_form.cleaned_data['country']
            order.save()

            for movie in movies_in_cart:
                item = Item()
                item.movie = movie
                item.price = movie.price
                item.order = order
                item.quantity = cart[str(movie.id)]
                item.save()

            request.session['cart'] = {}
            template_data = {}
            template_data['title'] = 'Purchase confirmation'
            template_data['order_id'] = order.id
            return render(request, 'cart/purchase.html', {'template_data': template_data})
        
        else:
            template_data = {}
            template_data['title'] = 'Checkout'
            template_data['movies_in_cart'] = movies_in_cart
            template_data['cart_total'] = cart_total
            template_data['location_form'] = location_form
            return render(request, 'cart/checkout.html', {'template_data': template_data})

@login_required
def purchase(request):
    # Redirect to checkout for proper location handling
    return redirect('cart.checkout')