from django.db import models
import time
import json


class JSONField(models.TextField):
    """
    自定义JSONField，用于存储JSON数据
    """

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return value

    def to_python(self, value):
        if isinstance(value, (dict, list)):
            return value
        if value is None:
            return value
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return value

    def get_prep_value(self, value):
        if value is None:
            return value
        return json.dumps(value, ensure_ascii=False)


class Issue(models.Model):
    issue_id = models.AutoField(db_column='id', primary_key=True)
    author = models.ForeignKey(to='usermanage.User', on_delete=models.DO_NOTHING, blank=True, null=True)
    title = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    date = models.DateField(blank=True, null=True)
    description = models.TextField()

    class Meta:
        managed = True
        db_table = 'issue'


def get_upload_path_for_original_image(instance, filename):
    """
    自定义图片上传路径
    :param instance: 当前实例
    :param filename: 文件名
    :return: 上传路径
    """
    return f'issue/{instance.issue.author.id}/{instance.issue.issue_id}/{str(time.time())}_{filename}'

def get_upload_path_for_detected_image(instance, filename):
    """
    自定义图片上传路径
    :param instance: 当前实例
    :param filename: 文件名
    :return: 上传路径
    """
    return f'detected/{instance.issue.author.id}/{instance.issue.issue_id}/detected_{str(time.time())}_{filename}'

def get_upload_path_for_relationship_image(instance, filename):
    """
    自定义图片上传路径
    :param instance: 当前实例
    :param filename: 文件名
    :return: 上传路径
    """
    return f'relationship/{instance.issue.author.id}/{instance.issue.issue_id}/relationship_{str(time.time())}_{filename}'


class Picture(models.Model):
    picture_id = models.AutoField(db_column='id', primary_key=True)
    issue = models.ForeignKey(to=Issue, on_delete=models.DO_NOTHING, blank=True, null=True)
    url = models.ImageField(upload_to=get_upload_path_for_original_image, blank=True, null=True)
    upload_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    relations = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    detected_image = models.ImageField(upload_to=get_upload_path_for_detected_image, blank=True, null=True)
    relationship_image = models.ImageField(upload_to=get_upload_path_for_relationship_image, blank=True, null=True)
    face_data = JSONField(blank=True, null=True)  # 新增：存储人脸标注信息

    class Meta:
        managed = True
        db_table = 'picture'