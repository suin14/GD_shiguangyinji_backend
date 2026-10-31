from django.http import JsonResponse, HttpResponse
from rest_framework.views import APIView
from utils.permissions import IsOwner
from rest_framework.permissions import IsAuthenticated
from .models import Video, VideoPicture
from issue.models import Picture, Issue
from character_db.models import Character
from usermanage.models import User
from utils.edit import generate_video_from_json, generate_conclusion
from .tasks import video_task_manager
import json
import os
import time
import threading
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone


class VideoManagement(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET接口：获取用户的视频列表或特定视频详情
        参数：video_id (可选) - 如果提供则返回特定视频详情，否则返回视频列表
        """
        user_id = request.user.id if request.user.is_authenticated else None
        if user_id is None:
            return JsonResponse({'error': 'User not authenticated'}, status=401)

        video_id = request.query_params.get('video_id')

        if video_id:
            # 返回特定视频的详情
            try:
                video = Video.objects.get(video_id=video_id, owner_id=user_id, status='completed')

                # 获取关联的图片
                video_pictures = VideoPicture.objects.filter(video=video).select_related('picture')
                picture_ids = [vp.picture.picture_id for vp in video_pictures]

                video_data = {
                    'video_id': video.video_id,
                    'title': video.title,
                    'description': video.description,
                    'event_title': video.event_title,
                    'video_url': f"/api/media/{video.video_url}" if video.video_url else None,
                    'script_url': f"/api/media/{video.script_url}" if video.script_url else None,
                    'upload_at': video.upload_at.isoformat() if video.upload_at else None,
                    'picture_ids': picture_ids,
                    'status': video.status,
                    'progress': video.progress,
                    'error_message': video.error_message,
                    'started_at': video.started_at.isoformat() if video.started_at else None,
                    'completed_at': video.completed_at.isoformat() if video.completed_at else None
                }
                return JsonResponse(video_data, status=200)

            except Video.DoesNotExist:
                return JsonResponse({'error': 'Video not found'}, status=404)
        else:
            # 返回用户的视频列表
            videos = Video.objects.filter(owner_id=user_id, status='completed').order_by('-upload_at')

            if not videos.exists():
                return JsonResponse({'videos': []}, status=200)

            video_list = []
            for video in videos:
                # 获取关联的图片作为封面候选
                video_pictures = VideoPicture.objects.filter(video=video).select_related('picture')

                # 随机选择一张图片作为封面
                thumbnail_url = None
                events = []

                if video_pictures.exists():
                    import random
                    random_picture = random.choice(list(video_pictures))
                    if random_picture.picture and random_picture.picture.url:
                        thumbnail_url = f"/api/media/{random_picture.picture.url}"

                # 处理事件数据（现在是JSONField）
                events = []
                if video.event_title and isinstance(video.event_title, list):
                    # 直接使用JSONField中的数据
                    events = video.event_title
                    # 确保每个事件都有必要的字段
                    for event in events:
                        if not event.get('id'):
                            event['id'] = len(events)
                        if not event.get('date'):
                            event['date'] = video.upload_at.strftime('%Y-%m-%d') if video.upload_at else None
                elif video.event_title and isinstance(video.event_title, str):
                    # 向后兼容：处理可能残留的字符串格式
                    try:
                        import json
                        if video.event_title.startswith('[') and video.event_title.endswith(']'):
                            events = json.loads(video.event_title)
                        else:
                            # 字符串分割格式
                            if ' | ' in video.event_title:
                                event_titles = video.event_title.split(' | ')
                                for i, title in enumerate(event_titles):
                                    if title.strip():
                                        events.append({
                                            'id': i + 1,
                                            'title': title.strip(),
                                            'date': video.upload_at.strftime('%Y-%m-%d') if video.upload_at else None
                                        })
                            else:
                                events.append({
                                    'id': 1,
                                    'title': video.event_title.strip(),
                                    'date': video.upload_at.strftime('%Y-%m-%d') if video.upload_at else None
                                })
                    except Exception as e:
                        print(f"处理事件数据失败: {e}")
                        events = []

                video_data = {
                    'id': video.video_id,  # 前端使用id字段
                    'video_id': video.video_id,
                    'title': video.title or '未命名视频',
                    'description': video.description or '暂无描述',
                    'event_title': video.event_title,
                    'video_url': f"/api/media/{video.video_url}" if video.video_url else None,
                    'videoUrl': f"/api/media/{video.video_url}" if video.video_url else None,  # 前端兼容
                    'thumbnail': thumbnail_url,  # 随机选择的封面
                    'date': video.upload_at.isoformat() if video.upload_at else None,
                    'upload_at': video.upload_at.isoformat() if video.upload_at else None,
                    'completed_at': video.completed_at.isoformat() if video.completed_at else None,  # 视频完成时间
                    'started_at': video.started_at.isoformat() if video.started_at else None,  # 视频开始生成时间
                    'status': video.status,
                    'progress': video.progress,
                    'events': events  # 包含的事件列表
                }
                video_list.append(video_data)

            return JsonResponse({'videos': video_list}, status=200)

    def post(self, request):
        """
        POST接口：串联回忆 - 接收图片ID列表和视频信息，异步生成视频
        支持覆盖已存在的视频
        """
        user_id = request.user.id if request.user.is_authenticated else None
        if user_id is None:
            return JsonResponse({'error': 'User not authenticated'}, status=401)

        # 获取请求参数
        data = request.data.get('pictures')  # 图片ID列表
        video_title = request.data.get('title', '')  # 视频标题
        video_description = request.data.get('description', '')  # 内容描述
        video_id = request.data.get('video_id', None)  # 如果提供则覆盖现有视频

        # 新增参数
        use_digital_human = request.data.get('use_digital_human', False)  # 是否使用数字人开头
        enable_smart_animation = request.data.get('enable_smart_animation', True)  # 是否开启图片智能动态化
        digital_human_source = request.data.get('digital_human_source', 'existing')  # 数字人头像来源
        character_id = request.data.get('character_id', None)  # 角色ID（使用已有头像时）
        digital_human_avatar = request.FILES.get('digital_human_avatar', None)  # 上传的头像文件

        if not data:
            return JsonResponse({'error': 'No pictures provided'}, status=400)

        try:
            p_id_list = json.loads(data) if isinstance(data, str) else data
        except (json.JSONDecodeError, TypeError):
            return JsonResponse({'error': 'Invalid pictures data format'}, status=400)

        if not isinstance(p_id_list, list) or not p_id_list:
            return JsonResponse({'error': 'Pictures must be a non-empty list'}, status=400)

        try:
            # 验证图片是否存在
            for pic_id in p_id_list:
                if not Picture.objects.filter(picture_id=pic_id).exists():
                    return JsonResponse({'error': f'Picture {pic_id} not found'}, status=404)

            # 处理上传的数字人头像文件
            digital_human_avatar_path = None
            if digital_human_avatar and digital_human_source == 'upload':
                try:
                    import tempfile
                    import shutil
                    from django.core.files.storage import default_storage

                    # 创建临时文件
                    temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_uploads')
                    os.makedirs(temp_dir, exist_ok=True)

                    # 生成唯一的临时文件名
                    import time
                    temp_filename = f"temp_avatar_{int(time.time())}_{digital_human_avatar.name}"
                    temp_file_path = os.path.join(temp_dir, temp_filename)

                    # 保存上传的文件到临时位置
                    with open(temp_file_path, 'wb') as temp_file:
                        for chunk in digital_human_avatar.chunks():
                            temp_file.write(chunk)

                    digital_human_avatar_path = temp_file_path
                    print(f"临时头像文件已保存: {digital_human_avatar_path}")

                except Exception as e:
                    print(f"保存临时头像文件失败: {e}")
                    return JsonResponse({'error': f'Failed to save avatar file: {str(e)}'}, status=500)

            # 检查是否是覆盖操作
            video_obj = None
            if video_id:
                try:
                    video_obj = Video.objects.get(video_id=video_id, owner_id=user_id)
                    print(f"找到现有视频，将进行覆盖: {video_obj.video_id}")
                except Video.DoesNotExist:
                    return JsonResponse({'error': 'Video not found or not owned by user'}, status=404)
            else:
                # 创建新视频记录
                video_obj = Video.objects.create(
                    owner_id=user_id,
                    title=video_title,
                    description=video_description,
                    status='pending',
                    progress=0
                )
                video_id = video_obj.video_id
                print(f"新视频记录创建成功: {video_obj.video_id}")

            # 启动异步任务，传递临时文件路径而不是文件对象
            task_started = video_task_manager.start_video_generation(
                video_id, user_id, p_id_list, video_title, video_description,
                use_digital_human, enable_smart_animation, digital_human_source,
                character_id, digital_human_avatar_path
            )

            if not task_started:
                return JsonResponse({'error': 'Video generation task already running'}, status=409)

            # 返回成功响应
            return JsonResponse({
                'video_id': video_id,
                'status': 'processing',
                'progress': 0,
                'message': '视频生成任务已启动，请稍候...',
                'title': video_title,
                'description': video_description
            }, status=202)  # 202 Accepted

        except Exception as e:
            print(f"启动视频生成任务时出错: {str(e)}")
            return JsonResponse({'error': f'Failed to start video generation: {str(e)}'}, status=500)



    def delete(self, request):
        """
        DELETE接口：删除指定的视频
        参数：video_id - 要删除的视频ID
        """
        user_id = request.user.id if request.user.is_authenticated else None
        if user_id is None:
            return JsonResponse({'error': 'User not authenticated'}, status=401)

        video_id = request.query_params.get('video_id')
        if not video_id:
            return JsonResponse({'error': 'Video ID is required'}, status=400)

        try:
            video = Video.objects.get(video_id=video_id, owner_id=user_id)

            # 删除物理文件
            if video.video_url:
                video_path = os.path.join(settings.MEDIA_ROOT, video.video_url)
                if os.path.exists(video_path):
                    os.remove(video_path)
                    print(f"删除视频文件: {video_path}")

            if video.script_url:
                script_path = os.path.join(settings.MEDIA_ROOT, video.script_url)
                if os.path.exists(script_path):
                    os.remove(script_path)
                    print(f"删除脚本文件: {script_path}")

            # 删除数据库记录（VideoPicture会因为CASCADE自动删除）
            video.delete()

            return JsonResponse({'message': 'Video deleted successfully'}, status=200)

        except Video.DoesNotExist:
            return JsonResponse({'error': 'Video not found'}, status=404)
        except Exception as e:
            print(f"删除视频时出错: {str(e)}")
            return JsonResponse({'error': f'Failed to delete video: {str(e)}'}, status=500)


class VideoStatusView(APIView):
    """视频状态查询接口"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET接口：查询视频生成状态
        参数：video_id - 视频ID
        """
        user_id = request.user.id if request.user.is_authenticated else None
        if user_id is None:
            return JsonResponse({'error': 'User not authenticated'}, status=401)

        video_id = request.query_params.get('video_id')
        if not video_id:
            return JsonResponse({'error': 'Video ID is required'}, status=400)

        try:
            video = Video.objects.get(video_id=video_id, owner_id=user_id)

            # 获取任务状态
            task_status = video_task_manager.get_task_status(video_id)

            response_data = {
                'video_id': video.video_id,
                'status': video.status,
                'progress': video.progress,
                'error_message': video.error_message,
                'started_at': video.started_at.isoformat() if video.started_at else None,
                'completed_at': video.completed_at.isoformat() if video.completed_at else None,
                'task_active': task_status.get('active', False),
                'video_url': f"/api/media/{video.video_url}" if video.video_url and video.status == 'completed' else None
            }

            return JsonResponse(response_data, status=200)

        except Video.DoesNotExist:
            return JsonResponse({'error': 'Video not found'}, status=404)
        except Exception as e:
            print(f"查询视频状态时出错: {str(e)}")
            return JsonResponse({'error': f'Failed to get video status: {str(e)}'}, status=500)


class VideoSaveView(APIView):
    """视频保存接口"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        POST接口：保存视频（用户确认满意后调用）
        参数：video_id - 视频ID
        """
        user_id = request.user.id if request.user.is_authenticated else None
        if user_id is None:
            return JsonResponse({'error': 'User not authenticated'}, status=401)

        video_id = request.data.get('video_id')
        if not video_id:
            return JsonResponse({'error': 'Video ID is required'}, status=400)

        try:
            video = Video.objects.get(video_id=video_id, owner_id=user_id)

            if video.status != 'completed':
                return JsonResponse({'error': 'Video is not completed yet'}, status=400)

            # 这里可以添加额外的保存逻辑，比如移动文件到永久存储位置
            # 目前只是标记为已保存
            # video.upload_at = timezone.now()
            video.save()

            return JsonResponse({
                'message': 'Video saved successfully',
                'video_id': video.video_id,
                'video_url': f"/api/media/{video.video_url}"
            }, status=200)

        except Video.DoesNotExist:
            return JsonResponse({'error': 'Video not found'}, status=404)
        except Exception as e:
            print(f"保存视频时出错: {str(e)}")
            return JsonResponse({'error': f'Failed to save video: {str(e)}'}, status=500)


