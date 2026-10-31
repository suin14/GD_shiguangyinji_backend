# Generated manually to fix event dates in event_title field

from django.db import migrations


def fix_event_dates(apps, schema_editor):
    """修复event_title中的日期，使用Issue的date而不是video的upload_at"""
    Video = apps.get_model('video', 'Video')
    VideoPicture = apps.get_model('video', 'VideoPicture')
    Picture = apps.get_model('issue', 'Picture')
    Issue = apps.get_model('issue', 'Issue')
    
    for video in Video.objects.all():
        if video.event_title and isinstance(video.event_title, list):
            try:
                # 获取视频关联的图片
                video_pictures = VideoPicture.objects.filter(video=video)
                picture_ids = [vp.picture_id for vp in video_pictures]
                
                if not picture_ids:
                    continue
                
                # 获取图片及其关联的Issue
                pictures = Picture.objects.filter(picture_id__in=picture_ids).select_related('issue')
                
                # 按Issue分组
                issue_groups = {}
                for picture in pictures:
                    if picture.issue:
                        issue_id = picture.issue.issue_id
                        if issue_id not in issue_groups:
                            issue_groups[issue_id] = {
                                'issue': picture.issue,
                                'pictures': []
                            }
                        issue_groups[issue_id]['pictures'].append(picture)
                
                # 重新构建event_title数组
                new_events = []
                event_id = 1
                for issue_id, group in issue_groups.items():
                    issue = group['issue']
                    
                    # 使用Issue的信息
                    event_title = issue.title or f"事件{event_id}"
                    # 使用Issue的date字段
                    event_date = issue.date.strftime('%Y-%m-%d') if issue.date else '2025-01-01'
                    
                    event_data = {
                        'id': event_id,
                        'title': event_title,
                        'date': event_date
                    }
                    
                    new_events.append(event_data)
                    event_id += 1
                
                # 按日期排序
                new_events.sort(key=lambda x: x['date'])
                
                # 更新视频的event_title
                if new_events:
                    video.event_title = new_events
                    video.save()
                    print(f"修复视频 {video.video_id} 的事件日期，共 {len(new_events)} 个事件")
                
            except Exception as e:
                print(f"修复视频 {video.video_id} 的事件日期失败: {e}")


def reverse_fix_event_dates(apps, schema_editor):
    """回滚操作：恢复使用upload_at作为日期"""
    Video = apps.get_model('video', 'Video')
    
    for video in Video.objects.all():
        if video.event_title and isinstance(video.event_title, list):
            try:
                # 将所有事件的日期改回video的upload_at
                for event in video.event_title:
                    event['date'] = video.upload_at.strftime('%Y-%m-%d') if video.upload_at else '2025-01-01'
                
                video.save()
                print(f"回滚视频 {video.video_id} 的事件日期")
                
            except Exception as e:
                print(f"回滚视频 {video.video_id} 的事件日期失败: {e}")


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0002_alter_video_event_title'),
        ('issue', '0004_picture_face_data'),  # 确保issue应用的迁移已完成
    ]

    operations = [
        migrations.RunPython(
            code=fix_event_dates,
            reverse_code=reverse_fix_event_dates,
        ),
    ]
