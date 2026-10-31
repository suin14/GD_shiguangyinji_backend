from django.db import models
import time

def get_upload_path(instance, filename):
    """
    自定义图片上传路径
    :param instance: 当前实例
    :param filename: 文件名
    :return: 上传路径
    """
    return f'character_db/{instance.belongs_to.id}/{instance.character_id}/{time.time()}_{filename}'


GENDER_CHOICES = [('male', '男'), ('female', '女')]


class FloatListField(models.Field):
    """
    自定义ListField，存储浮点数列表
    """
    
    description = "List of floats"

    def db_type(self, connection):
        return 'text'

    def from_db_value(self, value, expression, connection):
        if value is None or value == '':
            return value
        return [float(i) for i in value.split(',')]

    def to_python(self, value):
        if isinstance(value, list):
            return value
        if value is None:
            return value
        return [float(i) for i in value.split(',')]

    def get_prep_value(self, value):
        if not value:
            return ''
        return ','.join(map(str, value))


class Character(models.Model):
    character_id = models.AutoField(db_column='id', primary_key=True)
    avatar = models.ImageField(upload_to=get_upload_path, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    belongs_to = models.ForeignKey(to='usermanage.User', on_delete=models.DO_NOTHING, blank=True, null=True)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES, default='male')
    relationship = models.CharField(max_length=255, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    face_data = FloatListField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'character'
