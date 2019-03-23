from django.urls import path
from .views import InstaGroupView


urlpatterns = [
    path('<insta_group>', InstaGroupView.as_view(), name='insta_group'),
]
