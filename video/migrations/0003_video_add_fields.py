# Generated manually for video model field additions

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("video", "0002_alter_video_options_alter_video_table"),
    ]

    operations = [
        migrations.AddField(
            model_name="video",
            name="title",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="video",
            name="description",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="video",
            name="event_title",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="video",
            name="status",
            field=models.CharField(
                choices=[
                    ('pending', '等待生成'),
                    ('processing', '正在生成'),
                    ('completed', '生成完成'),
                    ('failed', '生成失败'),
                ],
                default='pending',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name="video",
            name="progress",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="video",
            name="error_message",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="video",
            name="started_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="video",
            name="completed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
