from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist
import django.views.generic as generic

from .tasks import *
from .models import *

def main(request):
    template = loader.get_template('main_page.html')
    search_params = {k: request.GET.get(k) for k in ('query', 'max_depth')}
    context = dict()
    if not search_params['query'] is None:
        search_params['max_depth'] = int(search_params['max_depth'])
        print(search_params)
        article_dois = search_outer.delay(**search_params).get()
        context['articles'] = Article.objects.filter(doi__in=article_dois)
    return HttpResponse(template.render(context, request))

def result(request):
    template = loader.get_template('result_page.html')
    context = dict()
    return HttpResponse(template.render(context, request))
