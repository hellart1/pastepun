from django.urls import path, include
from .views import *
from django.conf import settings


urlpatterns = [
    path('', Home.as_view(), name='home'),
    path('edit/<str:data>', EditPaste.as_view(), name='edit_paste'),
    path('<str:data>', PasteDetail.as_view(), name='paste_detail'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns