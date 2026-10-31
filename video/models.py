from django.db import models
import json


class Video(models.Model):
    # 视频状态选择
    STATUS_CHOICES = [
        ('pending', '等待生成'),
        ('processing', '正在生成'),
        ('completed', '生成完成'),
        ('failed', '生成失败'),
    ]

    video_id = models.AutoField(db_column='id', primary_key=True)
    script_url = models.CharField(max_length=255, blank=True, null=True)
    video_url = models.CharField(max_length=255, blank=True, null=True)
    owner = models.ForeignKey(to='usermanage.User', on_delete=models.DO_NOTHING, blank=True, null=True)
    upload_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255, blank=True, null=True)  # 视频标题
    description = models.TextField(blank=True, null=True)  # 内容方向描述
    event_title = models.JSONField(default=list, blank=True, null=True)  # 选择事件的列表 [{"id":1,"title":"攀登黄山","date":"2025-05-27"}]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  # 生成状态
    progress = models.IntegerField(default=0)  # 生成进度 (0-100)
    error_message = models.TextField(blank=True, null=True)  # 错误信息
    started_at = models.DateTimeField(blank=True, null=True)  # 开始生成时间
    completed_at = models.DateTimeField(blank=True, null=True)  # 完成生成时间

    class Meta:
        managed = True
        db_table = 'video'


class VideoTask(models.Model):
    task_id = models.CharField(max_length=255, primary_key=True)
    video_path = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        managed = True
        db_table = 'video_task'


class VideoPicture(models.Model):
    video_picture_id = models.AutoField(db_column='id', primary_key=True)
    video = models.ForeignKey(to=Video, on_delete=models.CASCADE, blank=True, null=True)
    picture = models.ForeignKey(to='issue.Picture', on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'video_picture'