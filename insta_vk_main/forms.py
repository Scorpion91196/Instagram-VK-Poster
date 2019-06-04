from django import forms
from .models import UserSettings, CustomUser


class SettingsForm(forms.ModelForm):

    class Meta:
        model = UserSettings
        fields = 'insta_login', 'insta_password', 'vk_login', 'vk_password', 'vk_token', 'vk_app', 'vk_group_id'
        widgets = {
            'insta_password': forms.PasswordInput(),
            'vk_password': forms.PasswordInput()
        }


class LoginForm(forms.Form):
    username = forms.CharField(label='Логин', help_text='')
    password = forms.CharField(widget=forms.PasswordInput(), label="Пароль", help_text='')

    def clean(self):
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        if CustomUser.objects.filter(username=username).exists():
            try:
                CustomUser.objects.get(username=username).user_settings
            except:
                raise forms.ValidationError("Пользователя с таким логином не существует")
        else:
            raise forms.ValidationError("Пользователя с таким логином не существует")
        user = CustomUser.objects.get(username=username)
        print(user.password)
        print(password)
        if not user.check_password(password):
            raise forms.ValidationError("Введен неверный пароль")


class RegistrationForm(forms.ModelForm):
    password_check = forms.CharField(widget=forms.PasswordInput)
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")

    class Meta:
        model = CustomUser
        fields = [
            'username',
            'password',
            'password_check',
            'email'
        ]

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['username'].label = 'Логин'
        self.fields['username'].help_text = 'Обязательное поле'
        self.fields['password_check'].label = 'Подтвердите пароль'

    def clean(self):
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        password_check = self.cleaned_data['password_check']
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError('Пользователь с таким именем уже существует')
        if password != password_check:
            raise forms.ValidationError('Пароли не совпадают')
