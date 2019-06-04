"""insta_vk_poster URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from insta_vk_main.views import MainPageView, LoginView, LogoutView, UserSettingsView, RegistrationView, SendPosts, AcceptRegistration

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', MainPageView.as_view(), name='main_page'),
    path('insta-group/', include('instagram_api.urls')),
    path('settings', UserSettingsView.as_view(), name='settings'),
    path('login', LoginView.as_view(), name='login'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('registration', RegistrationView.as_view(), name='registration'),
    path('send-posts', SendPosts.as_view(), name='send-posts'),
    path('accept_registration/<registration_code>', AcceptRegistration.as_view(), name='accept-registration')
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
