from django.urls import path

from .views import *

urlpatterns = [
    path('', ProxyListView.as_view(), name='proxy_list')
]
