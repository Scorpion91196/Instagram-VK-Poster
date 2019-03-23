from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.views import View
from .models import InstaVkUser, InstaGroup
from .forms import LoginForm, SettingsForm, RegistrationForm

import time
import datetime
import vk_api
import json
import requests
from io import BytesIO


class MainPageView(View):
    def get(self, request, *args, **kwargs):
        if request.GET.get('add_insta_group') and request.GET.get('add_insta_group') != '':
            insta_name = request.GET.get('add_insta_group')
            print(insta_name)
            new_insta_group = InstaGroup.objects.create(name=insta_name)
            new_insta_group.save()
            request.user.user_settings.insta_group_list.add(new_insta_group)
            return HttpResponseRedirect('/')

        if request.user.is_authenticated:
            user_insta_groups = request.user.user_settings.insta_group_list.all()
            context = {
                'user_insta_groups': user_insta_groups
            }
            return render(request, 'index.html', context)
        else:
            return HttpResponseRedirect("login")


class UserSettingsView(View):
    def get(self, request, *args, **kwargs):
        user_settings = request.user.user_settings
        settings_form = SettingsForm()
        settings_form.user_id = request.user

        if user_settings.insta_login != 'None' and user_settings.insta_login is not None:
            settings_form.fields['insta_login'].widget.attrs['value'] = user_settings.insta_login
        else:
            settings_form.fields['insta_login'].widget.attrs['value'] = ''

        if user_settings.insta_password != 'None' and user_settings.insta_password is not None:
            settings_form.fields['insta_password'].widget.attrs['value'] = user_settings.insta_password
        else:
            settings_form.fields['insta_password'].widget.attrs['value'] = ''

        if user_settings.vk_login != 'None' and user_settings.vk_login is not None:
            settings_form.fields['vk_login'].widget.attrs['value'] = user_settings.vk_login
        else:
            settings_form.fields['vk_login'].widget.attrs['value'] = ''

        if user_settings.vk_password != 'None' and user_settings.vk_password is not None:
            settings_form.fields['vk_password'].widget.attrs['value'] = user_settings.vk_password
        else:
            settings_form.fields['vk_password'].widget.attrs['value'] = ''

        if user_settings.vk_token != 'None' and user_settings.vk_token is not None:
            settings_form.fields['vk_token'].widget.attrs['value'] = user_settings.vk_token
        else:
            settings_form.fields['vk_token'].widget.attrs['value'] = ''

        if user_settings.vk_app != 'None' and user_settings.vk_app is not None:
            settings_form.fields['vk_app'].widget.attrs['value'] = user_settings.vk_app
        else:
            settings_form.fields['vk_app'].widget.attrs['value'] = ''

        if user_settings.vk_group_id != 'None' and user_settings.vk_group_id is not None:
            settings_form.fields['vk_group_id'].widget.attrs['value'] = user_settings.vk_group_id
        else:
            settings_form.fields['vk_group_id'].widget.attrs['value'] = ''

        context = {
            'user_settings': user_settings,
            'settings_form': settings_form
        }
        return render(request, 'settings.html', context)

    def post(self, request, *args, **kwargs):
        if SettingsForm.is_valid:
            user_settings = request.user.user_settings
            user_settings.insta_login = request.POST.get('insta_login')
            user_settings.insta_password = request.POST.get('insta_password')
            user_settings.vk_login = request.POST.get('vk_login')
            user_settings.vk_password = request.POST.get('vk_password')
            user_settings.vk_token = request.POST.get('vk_token')
            user_settings.vk_app = request.POST.get('vk_app')
            user_settings.vk_group_id = request.POST.get('vk_group_id')
            user_settings.save()
        return HttpResponseRedirect('settings')


class SendPosts(View):
    def post(self, request, *args, **kwargs):
        user_settings = request.user.user_settings
        ready_items = json.loads(self.request.POST.get('ready_items'))
        first_post_now = json.loads(self.request.POST.get('first_post_now'))
        post_description = json.loads(self.request.POST.get('post_description'))
        interval = json.loads(self.request.POST.get('interval'))

        vk_session = vk_api.VkApi(user_settings.vk_login, user_settings.vk_password, user_settings.vk_token, app_id=user_settings.vk_app)
        vk_session.auth()
        vk = vk_session.get_api()
        upload_settings = vk.photos.getWallUploadServer(group_id=user_settings.vk_group_id)
        print(ready_items, first_post_now, post_description, type(interval))

        if first_post_now and interval != 0:
            img_response = requests.get(ready_items[0]['link'])
            if img_response.ok:
                vk_photo_response = requests.post(upload_settings['upload_url'], files={
                    'photo': ('file.jpg', BytesIO(img_response.content), 'image/jpg')})
                saved_photo = vk.photos.saveWallPhoto(group_id=user_settings.vk_group_id,
                                                      photo=vk_photo_response.json()['photo'],
                                                      server=vk_photo_response.json()['server'],
                                                      hash=vk_photo_response.json()['hash'])
                vk.wall.post(owner_id='-' + user_settings.vk_group_id, message=ready_items[0]['descr'], from_group='1',
                             attachments='photo' + str(saved_photo[0]['owner_id']) + '_' + str(saved_photo[0]['id']))
            if len(ready_items) > 1:
                count = 1
                for item in ready_items[1:]:
                    img_response = requests.get(item['link'])
                    if img_response.ok:
                        timenow = int(time.time())
                        vk_photo_response = requests.post(upload_settings['upload_url'], files={'photo': ('file.jpg', BytesIO(img_response.content), 'image/jpg')})
                        saved_photo = vk.photos.saveWallPhoto(group_id=user_settings.vk_group_id,
                                                              photo=vk_photo_response.json()['photo'],
                                                              server=vk_photo_response.json()['server'],
                                                              hash=vk_photo_response.json()['hash'])
                        vk.wall.post(owner_id='-'+user_settings.vk_group_id, message=item['descr'], from_group='1', publish_date=str(timenow+interval*60*count),
                                     attachments='photo'+str(saved_photo[0]['owner_id'])+'_'+str(saved_photo[0]['id']))
                        count += 1
        elif not first_post_now and interval != 0:
            print("Все посты постим с интервалом "+str(interval)+" мин.")
            count = 1
            for item in ready_items:
                img_response = requests.get(item['link'])
                if img_response.ok:
                    timenow = int(time.time())
                    vk_photo_response = requests.post(upload_settings['upload_url'], files={
                        'photo': ('file.jpg', BytesIO(img_response.content), 'image/jpg')})
                    saved_photo = vk.photos.saveWallPhoto(group_id=user_settings.vk_group_id,
                                                          photo=vk_photo_response.json()['photo'],
                                                          server=vk_photo_response.json()['server'],
                                                          hash=vk_photo_response.json()['hash'])
                    vk.wall.post(owner_id='-' + user_settings.vk_group_id, message=item['descr'], from_group='1',
                                 publish_date=str(timenow + interval * 60 * count),
                                 attachments='photo' + str(saved_photo[0]['owner_id']) + '_' + str(
                                     saved_photo[0]['id']))
                    count += 1
        else:
            print("Постим все сразу!!!")
            for item in ready_items:
                img_response = requests.get(item['link'])
                if img_response.ok:
                    vk_photo_response = requests.post(upload_settings['upload_url'], files={'photo': ('file.jpg', BytesIO(img_response.content), 'image/jpg')})
                    saved_photo = vk.photos.saveWallPhoto(group_id=user_settings.vk_group_id,
                                                          photo=vk_photo_response.json()['photo'],
                                                          server=vk_photo_response.json()['server'],
                                                          hash=vk_photo_response.json()['hash'])
                    vk.wall.post(owner_id='-'+user_settings.vk_group_id, message=item['descr'], from_group='1',
                                 attachments='photo'+str(saved_photo[0]['owner_id'])+'_'+str(saved_photo[0]['id']))

        return JsonResponse({'response': 'success'})


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = LoginForm(request.POST or None)
        context = {
            'login_form': form
        }
        return render(request, 'login.html', context)

    def post(self, request, *args, **kwargs):
        form = LoginForm(request.POST or None)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
            return HttpResponseRedirect('/')
        context = {
            'login_form': form
        }
        return render(self.request, 'login.html', context)


class LogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return HttpResponseRedirect('login')


class RegistrationView(View):
    def get(self, request, *args, **kwargs):
        context = {
            'registration_form': RegistrationForm
        }
        return render(request, 'registration.html', context)

    def post(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST or None)
        if form.is_valid():
            username = request.POST.get('username')
            password = request.POST.get('password')
            email = request.POST.get('email')
            new_user = User.objects.create_user(username, email, password)
            new_user.save()
            new_insta_vk_user = InstaVkUser.objects.create(user=new_user)
            new_insta_vk_user.save()
            return render(request, 'successful_registration.html')
        context = {
            'registration_form': form
        }
        return render(request, 'registration.html', context)
