from django.shortcuts import render
import django.views.generic as generic

from .models import *

class ProxyListView(generic.list.ListView):

    model = Proxy
    context_object_name = 'proxies'
