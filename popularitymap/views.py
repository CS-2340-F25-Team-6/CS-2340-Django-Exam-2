import json
from django.shortcuts import render
from django.conf import settings

# Create your views here.
def index(request):
    template_data = {}
    template_data['google_api_key'] = settings.GOOGLE_API_KEY

    # TODO This is mock data, replace with the actual model
    # TODO Make sure when adding data to model, names match up with the GeoJSON in movestore/static
    popularity_data = {
        'Alabama': [
            {'movie': 'The Godfather', 'count': 245},
            {'movie': 'The Penguin', 'count': 285},
            {'movie': 'The Quack', 'count': 170},
        ],
        'California': [
            {'movie': 'The Godfather', 'count': 245},
            {'movie': 'The Penguin', 'count': 285},
            {'movie': 'The Quack', 'count': 170},
        ],
    }
    # TODO MAKE SURE YOU SORT THE DATA BY COUNT BEFORE PASSING IT IN
    # TODO YOU MAY NEED TO UDPATE INDEX.HTML FOR THIS
    # TODO BASE IT OFF THE NEWLY ADDED STATE/COUNTRY IN ORDER MODEL

    template_data['popularity_data'] = json.dumps(popularity_data)

    return render(request, 'popularitymap/index.html', {'template_data': template_data})