from django.urls import path
from django.views.generic import TemplateView, RedirectView
from .views import map_view, geocode_proxy

urlpatterns = [
    path('', RedirectView.as_view(url='/map/', permanent=True)),
    path('map/', map_view, name='map'),
    path('about/', TemplateView.as_view(template_name='mapa/about.html'), name='about'),
    path('geocode/', geocode_proxy, name='geocode_proxy')
]