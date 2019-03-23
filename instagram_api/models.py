from django.db import models


class InstaGroup(models.Model):
    name = models.CharField(max_length=100)
    link = models.CharField(max_length=250)

    class Meta:
        verbose_name = "Instagram группа"
        verbose_name_plural = "Instagram группы"

    def __str__(self):
        return self.name
