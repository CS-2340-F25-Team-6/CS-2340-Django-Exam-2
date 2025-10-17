"""
Demo script to test the location feature functionality.
This script demonstrates:
1. Creating users with location information
2. Making purchases with location data
3. Viewing popularity map data based on purchases
"""

import os
import django
import sys

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviesstore.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile
from cart.models import Order, Item
from movies.models import Movie
from popularitymap.views import index as popularity_view
from django.test import RequestFactory

def create_demo_data():
    """Create demo users, movies, and orders with location data"""
    
    print("Creating demo data...")
    
    # Create demo users with locations
    users_data = [
        {'username': 'user_ca', 'password': 'testpass123', 'state': 'California', 'country': 'United States'},
        {'username': 'user_tx', 'password': 'testpass123', 'state': 'Texas', 'country': 'United States'},
        {'username': 'user_ny', 'password': 'testpass123', 'state': 'New York', 'country': 'United States'},
        {'username': 'user_ca2', 'password': 'testpass123', 'state': 'California', 'country': 'United States'},
    ]
    
    created_users = []
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={'password': user_data['password']}
        )
        if created:
            profile, _ = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'state': user_data['state'],
                    'country': user_data['country']
                }
            )
            print(f"Created user: {user.username} from {profile.state}")
        created_users.append(user)
    
    # Get existing movies or create some demo ones
    movies = list(Movie.objects.all())
    if not movies:
        print("No movies found. Please add movies through the admin interface first.")
        return
    
    # Create demo orders with location data
    orders_data = [
        {'user': created_users[0], 'state': 'California', 'movies': [movies[0], movies[1]], 'quantities': [2, 1]},
        {'user': created_users[1], 'state': 'Texas', 'movies': [movies[0], movies[2]], 'quantities': [1, 3]},
        {'user': created_users[2], 'state': 'New York', 'movies': [movies[1], movies[2]], 'quantities': [2, 1]},
        {'user': created_users[3], 'state': 'California', 'movies': [movies[0], movies[1]], 'quantities': [1, 2]},
    ]
    
    for order_data in orders_data:
        # Calculate total
        total = sum(movie.price * qty for movie, qty in zip(order_data['movies'], order_data['quantities']))
        
        order = Order.objects.create(
            user=order_data['user'],
            total=total,
            state=order_data['state'],
            country='United States'
        )
        
        # Create items for this order
        for movie, quantity in zip(order_data['movies'], order_data['quantities']):
            Item.objects.create(
                order=order,
                movie=movie,
                price=movie.price,
                quantity=quantity
            )
        
        print(f"Created order for {order.user.username} in {order.state} with {len(order_data['movies'])} items")
    
    print("Demo data created successfully!")

def test_popularity_data():
    """Test the popularity map data generation"""
    print("\nTesting popularity map data...")
    
    # Create a mock request
    factory = RequestFactory()
    request = factory.get('/popularity-map/')
    
    # Get the popularity data
    from popularitymap.views import index as popularity_index
    import json
    
    # Create a simple test to check if our view works
    from django.db.models import Q
    from cart.models import Order, Item
    
    # Get actual popularity data from orders
    popularity_data = {}
    
    orders_with_location = Order.objects.filter(
        Q(state__isnull=False) & ~Q(state__exact='')
    ).select_related('user')
    
    for order in orders_with_location:
        state = order.state
        if state not in popularity_data:
            popularity_data[state] = {}
        
        items = Item.objects.filter(order=order).select_related('movie')
        for item in items:
            movie_name = item.movie.name
            if movie_name not in popularity_data[state]:
                popularity_data[state][movie_name] = 0
            popularity_data[state][movie_name] += item.quantity
    
    # Format and display results
    print("Popularity data by state:")
    for state, movies in popularity_data.items():
        print(f"\n{state}:")
        movie_list = [{'movie': movie, 'count': count} for movie, count in movies.items()]
        movie_list.sort(key=lambda x: x['count'], reverse=True)
        for movie_data in movie_list:
            print(f"  {movie_data['movie']}: {movie_data['count']} purchases")

if __name__ == "__main__":
    print("Location Feature Demo")
    print("=" * 40)
    
    create_demo_data()
    test_popularity_data()
    
    print("\nDemo completed!")
    print("You can now:")
    print("1. Visit http://127.0.0.1:8000/accounts/signup/ to create a new user with location")
    print("2. Add movies to cart and checkout to test location selection")
    print("3. Visit http://127.0.0.1:8000/popularity-map/ to see the popularity map")