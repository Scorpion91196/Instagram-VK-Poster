from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.http import JsonResponse
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate, login, logout
from django.views import View
from .models import CustomUser, UserSettings, InstaGroup
from .forms import LoginForm, SettingsForm, RegistrationForm

import time, hashlib, vk_api, json, requests
from io import BytesIO


class MainPageView(View):
    def get(self, request, *args, **kwargs):
        if request.GET.get('add_insta_group') and request.GET.get('add_insta_group') != '':
            insta_name = request.GET.get('add_insta_group')
            new_insta_group, created = InstaGroup.objects.get_or_create(name=insta_name)
            CustomUser.objects.get(username=request.user.username).user_settings.insta_group_list.add(new_insta_group.id)
            return HttpResponseRedirect('/')

        if request.user.is_authenticated:
            user_insta_groups = CustomUser.objects.get(username=request.user.username).user_settings.insta_group_list.all()
            context = {
                'user_insta_groups': user_insta_groups
            }
            return render(request, 'index.html', context)
        else:
            return HttpResponseRedirect("login")


class UserSettingsView(View):
    def get(self, request, *args, **kwargs):
        user_settings = CustomUser.objects.get(username=request.user.username).user_settings
        settings_form = SettingsForm()
        settings_form.user_id = CustomUser.objects.get(username=request.user.username)

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
        user_insta_groups = CustomUser.objects.get(username=request.user.username).user_settings.insta_group_list.all()
        context = {
            'user_settings': user_settings,
            'settings_form': settings_form,
            'user_insta_groups': user_insta_groups
        }
        return render(request, 'settings.html', context)

    def post(self, request, *args, **kwargs):
        if SettingsForm.is_valid:
            user_settings = CustomUser.objects.get(username=request.user.username).user_settings
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
        user_settings = CustomUser.objects.get(username=request.user.username).user_settings
        ready_items = json.loads(self.request.POST.get('ready_items'))
        first_post_now = json.loads(self.request.POST.get('first_post_now'))
        interval = json.loads(self.request.POST.get('interval'))

        vk_session = vk_api.VkApi(user_settings.vk_login, user_settings.vk_password, user_settings.vk_token, app_id=user_settings.vk_app)
        vk_session.auth()
        vk = vk_session.get_api()
        upload_settings = vk.photos.getWallUploadServer(group_id=user_settings.vk_group_id)
        posts_in_future = vk.wall.get(owner_id='-'+user_settings.vk_group_id, filter='postponed')
        try:
            last_post_date = int(posts_in_future['items'][-1]['date'])
        except IndexError:
            last_post_date = 0

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
                timenow = int(time.time())
                for item in ready_items[1:]:
                    if last_post_date == 0:
                        publish_date = str(timenow + interval * 60 * count)
                    else:
                        publish_date = str(last_post_date + interval * 60 * count)
                    img_response = requests.get(item['link'])
                    if img_response.ok:
                        vk_photo_response = requests.post(upload_settings['upload_url'], files={'photo': ('file.jpg', BytesIO(img_response.content), 'image/jpg')})
                        saved_photo = vk.photos.saveWallPhoto(group_id=user_settings.vk_group_id,
                                                              photo=vk_photo_response.json()['photo'],
                                                              server=vk_photo_response.json()['server'],
                                                              hash=vk_photo_response.json()['hash'])
                        vk.wall.post(owner_id='-'+user_settings.vk_group_id, message=item['descr'], from_group='1', publish_date=publish_date,
                                     attachments='photo'+str(saved_photo[0]['owner_id'])+'_'+str(saved_photo[0]['id']))
                        count += 1
        elif not first_post_now and interval != 0:
            count = 1
            timenow = int(time.time())
            for item in ready_items:
                if last_post_date == 0:
                    publish_date = str(timenow + interval * 60 * count)
                else:
                    publish_date = str(last_post_date + interval * 60 * count)
                img_response = requests.get(item['link'])
                if img_response.ok:
                    vk_photo_response = requests.post(upload_settings['upload_url'], files={
                        'photo': ('file.jpg', BytesIO(img_response.content), 'image/jpg')})
                    saved_photo = vk.photos.saveWallPhoto(group_id=user_settings.vk_group_id,
                                                          photo=vk_photo_response.json()['photo'],
                                                          server=vk_photo_response.json()['server'],
                                                          hash=vk_photo_response.json()['hash'])
                    vk.wall.post(owner_id='-' + user_settings.vk_group_id, message=item['descr'], from_group='1',
                                 publish_date=publish_date,
                                 attachments='photo' + str(saved_photo[0]['owner_id']) + '_' + str(
                                     saved_photo[0]['id']))
                    count += 1
        else:
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

        return JsonResponse({'status': 'false'})


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
            salt = hashlib.sha3_256('python'.encode('utf-8')).hexdigest()
            register_code = hashlib.sha3_256(username.encode('utf-8')).hexdigest() + salt
            if request.META['REMOTE_HOST']:
                register_url = 'http://' + request.META['REMOTE_HOST'] + '/accept_registration/' + str(register_code)
                print(register_url)
            elif request.META['REMOTE_ADDR']:
                register_url = 'http://' + request.META['REMOTE_ADDR'] + '/accept_registration/' + str(register_code)
                print(register_url)
            CustomUser.objects.create_user(username, email, password, is_active=False, register_code=register_code)
            message = 'Для подтверждения регистрации перейдите по ссылке: ' + register_url
            send_mail(
                'Подтверждение регистрации',
                message,
                'jiumoh2011@yandex.ru',
                [email],
                fail_silently=False
            )
            return render(request, 'registration_email_access.html')
        context = {
            'registration_form': form
        }
        return render(request, 'registration.html', context)


class AcceptRegistration(View):
    def get(self, request, *args, **kwargs):
        registration_code = kwargs.get('registration_code')
        try:
            user = CustomUser.objects.get(register_code=registration_code, is_active=False)
            user.is_active = True
            user.save()
            UserSettings.objects.create(user=user)
            return render(request, 'successful_registration.html')
        except ObjectDoesNotExist:
            return HttpResponseRedirect('/')
