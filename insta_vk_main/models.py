from django.db import models
from django.contrib.auth.models import User
from instagram_api.models import InstaGroup


class InstaVkUser(models.Model):
    user = models.OneToOneField(User, related_name='user_settings', on_delete=models.CASCADE)
    insta_login = models.CharField(max_length=100, null=True, blank=True)
    insta_password = models.CharField(max_length=200, null=True, blank=True)
    vk_login = models.CharField(max_length=100, null=True, blank=True)
    vk_password = models.CharField(max_length=200, null=True, blank=True)
    vk_token = models.CharField(max_length=300, null=True, blank=True)
    vk_app = models.CharField(max_length=50, null=True, blank=True)
    vk_group_id = models.CharField(max_length=50, null=True, blank=True)
    insta_group_list = models.ManyToManyField(InstaGroup, blank=True)

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return "Пользователь "+self.user.username
