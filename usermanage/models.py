import time
from django.db import models
from django.contrib.auth.models import AbstractUser

def get_upload_path_for_avatar(instance, filename):
    """
    自定义图片上传路径
    :param instance: 当前实例
    :param filename: 文件名
    :return: 上传路径
    """
    return f'avatar/{instance.id}/{str(time.time())}_{filename}'


class User(AbstractUser):
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, null=True, blank=True)
    nickname = models.CharField(default="", max_length=255)
    introduction = models.CharField(default="", max_length=255)
    article = models.IntegerField(default=0)
    fans = models.IntegerField(default=0)
    avatar = models.ImageField(upload_to=get_upload_path_for_avatar, default='avatars/avatar.png', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'users'

    def __str__(self):
        return self.username
