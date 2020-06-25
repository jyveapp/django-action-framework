from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from rest_framework import routers

import daf.registry
from daf.tests import viewsets
import daf.urls


app_name = 'tests'
urlpatterns = [path('admin/', admin.site.urls)]
urlpatterns += daf.urls.get_url_patterns(
    daf.registry.interfaces().filter(
        action=daf.registry.actions().filter(app_label='tests'), namespace=''
    )
)

# Add DRF endpoints
router = routers.SimpleRouter()
router.register(r'user', viewsets.UserViewSet)
urlpatterns += router.urls

# Add static file hosting
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
