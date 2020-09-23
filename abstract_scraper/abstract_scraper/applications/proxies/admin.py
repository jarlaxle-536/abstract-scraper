from django.contrib import admin

from .models import *

class ProxyAdmin(admin.ModelAdmin):
    pass

admin.site.register(Proxy, ProxyAdmin)
