from django.urls import path

from ..views import ShortLinkRedirect


urlpatterns = [
    path('s/<id>/', ShortLinkRedirect.as_view(), name='short-link-redirect')
]
