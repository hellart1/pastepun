from django.urls import path, include
from .views import *
from django.conf import settings


urlpatterns = [
    path('', Home.as_view(), name='home'),
    path('api/paste/<str:hash>/', PasteAPIList.as_view(), name='paste_api'),
    path('edit/<str:data>', EditPaste.as_view(), name='edit_paste'),
    path('<str:data>', UserText.as_view(), name='user_text'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns