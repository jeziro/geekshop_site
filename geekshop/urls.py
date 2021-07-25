from django.conf.urls import include, patterns
from django.contrib import admin
import mainapp.views as mainapp

from django.conf import settings
from django.conf.urls.static import static

from django.urls import re_path, path

urlpatterns = [
    re_path(r'^$', mainapp.main, name='main'),
    re_path(r'^products/', include('mainapp.urls', namespace='products')),
    re_path(r'^contact/', mainapp.contact, name='contact'),
    re_path(r'^auth/', include('authapp.urls', namespace='auth')),
    re_path(r'^basket/', include('basketapp.urls', namespace='basket')),
    path('', include('social_django.urls', namespace='social')),
    re_path(r'^admin/', include('adminapp.urls', namespace='admin')),
    path('order/', include('ordersapp.urls', namespace='order')),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [re_path(r'^__debug__/', include(debug_toolbar.urls))]
