# Generated manually for event_title field type change

from django.db import migrations, models
import json


def convert_string_to_json(apps, schema_editor):
    """将现有的字符串格式event_title转换为JSON格式"""
    Video = apps.get_model('video', 'Video')
    
    for video in Video.objects.all():
        if video.event_title:
            try:
                # 如果已经是JSON格式，跳过
                if video.event_title.startswith('[') and video.event_title.endswith(']'):
                    # 尝试解析JSON
                    events = json.loads(video.event_title)
                    video.event_title = events
                    video.save()
                    continue
                
                # 转换字符串格式为JSON格式
                events = []
                if ' | ' in video.event_title:
                    # 分割格式: "事件1 | 事件2 | 事件3"
                    event_titles = video.event_title.split(' | ')
                    for i, title in enumerate(event_titles):
                        if title.strip():
                            events.append({
                                'id': i + 1,
                                'title': title.strip(),
                                'date': video.upload_at.strftime('%Y-%m-%d') if video.upload_at else '2025-01-01'
                            })
                else:
                    # 单个事件
                    events.append({
                        'id': 1,
                        'title': video.event_title.strip(),
                        'date': video.upload_at.strftime('%Y-%m-%d') if video.upload_at else '2025-01-01'
                    })
                
                video.event_title = events
                video.save()
                
            except Exception as e:
                print(f"转换视频 {video.video_id} 的event_title失败: {e}")
                # 如果转换失败，设置为空列表
                video.event_title = []
                video.save()


def convert_json_to_string(apps, schema_editor):
    """回滚：将JSON格式转换回字符串格式"""
    Video = apps.get_model('video', 'Video')
    
    for video in Video.objects.all():
        if video.event_title and isinstance(video.event_title, list):
            try:
                # 将JSON数组转换为字符串
                titles = [event.get('title', '') for event in video.event_title if event.get('title')]
                video.event_title = ' | '.join(titles) if titles else ''
                video.save()
            except Exception as e:
                print(f"回滚视频 {video.video_id} 的event_title失败: {e}")
                video.event_title = ''
                video.save()


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0001_initial'),
    ]

    operations = [
        # 第一步：添加临时字段
        migrations.AddField(
            model_name='video',
            name='event_title_json',
            field=models.JSONField(default=list, blank=True, null=True),
        ),
        
        # 第二步：数据迁移
        migrations.RunPython(
            code=convert_string_to_json,
            reverse_code=convert_json_to_string,
        ),
        
        # 第三步：删除旧字段
        migrations.RemoveField(
            model_name='video',
            name='event_title',
        ),
        
        # 第四步：重命名新字段
        migrations.RenameField(
            model_name='video',
            old_name='event_title_json',
            new_name='event_title',
        ),
    ]
