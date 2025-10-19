import json
from django.shortcuts import render
from django.conf import settings
from django.db.models import Count, Q
from cart.models import Order, Item

# Create your views here.
def index(request):
    template_data = {}
    template_data['google_api_key'] = settings.GOOGLE_API_KEY

    # Get actual popularity data from orders
    popularity_data = {}
    
    # Get all orders with state and country information
    orders_with_location = Order.objects.filter(
        Q(state__isnull=False) & ~Q(state__exact='')
    ).select_related('user')
    
    # Group orders by state and count movie purchases
    for order in orders_with_location:
        state = order.state
        if state not in popularity_data:
            popularity_data[state] = {}
        
        # Get all items in this order
        items = Item.objects.filter(order=order).select_related('movie')
        for item in items:
            movie_name = item.movie.name
            if movie_name not in popularity_data[state]:
                popularity_data[state][movie_name] = 0
            popularity_data[state][movie_name] += item.quantity
    
    # Convert to the format expected by the frontend and sort by count
    formatted_data = {}
    for state, movies in popularity_data.items():
        # Convert to list of dictionaries and sort by count (descending)
        movie_list = [{'movie': movie, 'count': count} for movie, count in movies.items()]
        movie_list.sort(key=lambda x: x['count'], reverse=True)
        formatted_data[state] = movie_list
    
    # If no real data exists, show a message or empty data
    if not formatted_data:
        # You can add some sample data for demonstration or leave empty
        formatted_data = {
            'No Data': [
                {'movie': 'No purchases yet', 'count': 0},
            ]
        }

    template_data['popularity_data'] = json.dumps(formatted_data)

    return render(request, 'popularitymap/index.html', {'template_data': template_data})