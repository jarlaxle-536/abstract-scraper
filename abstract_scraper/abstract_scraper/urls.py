from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('abstract_scraper.applications.main.urls')),
#    path('proxies/', include('abstract_scraper.applications.proxies.urls'))
]
