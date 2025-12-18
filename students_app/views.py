from django.shortcuts import render
from django.http import JsonResponse

# Create your views here.

def home(request):
    return JsonResponse({
    'title': 'Student Attitude & Behaviour API',
    'api_version': '1.0',
    'documentation_url': '<PENDING>',
    'links': {
        'self': {
            'href': '/',
            'methods': ['GET'],
            'rel': 'self',
        },
        'health': {
            'href': '/health',
            'methods': ['GET'],
            'rel': 'status',
        },
    },
})

def health(request):
    return JsonResponse({
        'service': 'Student Attitude & Behaviour API',
        'api_version': '1.0',
        'status': 'ok',
    })