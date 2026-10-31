from django.http import JsonResponse, HttpResponse, Http404
from rest_framework.views import APIView
from utils.permissions import IsOwner
from .models import Issue, Picture
from character_db.models import Character
from usermanage.models import User
import os
from django.conf import settings
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated, AllowAny
from utils.edit import load_event, load_known_people_single, expand_text
from rest_framework.response import Response
from django.core.files.base import ContentFile
import cv2
import mimetypes

class IssueManagement(APIView):
    permission_classes = [IsAuthenticated]
    who = 0

    def get(self, request):
        """
        GET接口：返回事件ID的列表
        """
        user_id = request.user.id if request.user.is_authenticated else None
        if user_id is None:
            return JsonResponse({'error': 'User not authenticated'}, status=401)

        if self.who == 0:
            event_ids = list(Issue.objects.filter(author_id=user_id).values_list('issue_id', flat=True))
        elif self.who == 1:
            event_ids = list(Issue.objects.exclude(author_id=user_id).values_list('issue_id', flat=True))
        else:
            event_ids = []  # 如果 `who` 不为 0 或 1，返回空列表

        if not event_ids:
            return JsonResponse({'event_ids': []}, status=200)
        return JsonResponse({'event_ids': event_ids}, status=200)

    def post(self, request):
        """
        POST接口：接收事件ID，返回事件的详细属性
        """
        issue_id = request.data.get('issue_id')
        if not issue_id:
            return JsonResponse({'error': 'Issue ID is required'}, status=400)

        try:
            issue = Issue.objects.get(issue_id=issue_id)
        except Issue.DoesNotExist:
            return JsonResponse({'error': 'Issue not found'}, status=404)

        # 获取图片数据，包括face_data
        pictures = Picture.objects.filter(issue=issue)
        picture_list = []
        for pic in pictures:
            picture_data = {
                'picture_id': pic.picture_id,
                'url': os.path.join(settings.MEDIA_URL, str(pic.url)),
                'description': pic.description,
                'location': pic.location,
                'face_data': pic.face_data
            }
            picture_list.append(picture_data)

        issue_data = {
            'issue_id': issue.issue_id,
            'author': issue.author.username if issue.author else None,
            'title': issue.title,
            'location': issue.location,
            'date': issue.date.strftime('%Y-%m-%d') if issue.date else None,
            'pictures': picture_list,
            'description': issue.description
        }
        return JsonResponse(issue_data, status=200)


class IssueCreate(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        POST接口：接收事件的详细属性，创建新的事件
        """
        user_id = request.user.id if request.user.is_authenticated else None
        if user_id is None:
            return JsonResponse({'error': 'User not authenticated'}, status=401)

        author = request.user
        location = request.data.get('location')
        date = request.data.get('date')
        title = request.data.get('title')
        pictures = request.FILES.getlist('pictures')
        description = request.data.get('description')

        issue = Issue.objects.create(
            author=author,
            title=title,
            location=location,
            date=date,
            description=description
        )
        for pic in pictures:
            if pic.name.endswith(settings.IMAGE_TAIL):
                Picture.objects.create(issue=issue, url=pic, location=location)

        me = Character.objects.filter(belongs_to=author.id, relationship='自己').first()
        if not me:
            return JsonResponse({'error': 'Character not found'}, status=401)
        protagonist = {
            'name': me.name,
            'avatar': os.path.join(settings.MEDIA_ROOT, str(me.avatar)).replace('\\', '/')
        }
        my_friends = Character.objects.filter(belongs_to=author).all()
        user_characters=[]
        for friend in my_friends:
            # if friend.relationship == '自己':
            #     continue
            friend_data = {
                'name': friend.name,
                'avatar': os.path.join(settings.MEDIA_ROOT, str(friend.avatar)).replace('\\', '/'),
                'relationship': friend.relationship,
                'face_data': friend.face_data
            }
            user_characters.append(friend_data)
        event_list = []
        events = Picture.objects.filter(issue=issue).all()
        for event in events:
            event_list.append({'id':event.picture_id,'url':os.path.join(settings.MEDIA_ROOT, str(event.url)).replace('\\', '/')})
        print(event_list)
        infos = load_event(protagonist, user_characters, description, date, event_list, issue.issue_id)
        for info in infos:
            update_pic = Picture.objects.get(picture_id=info['id'])
            update_pic.description = info['description']
            update_pic.location = info['location']
            update_pic.relations = info['relations']

            # 处理 face_data（人脸标注信息）
            face_data = info.get('face_data')
            if face_data is not None:
                update_pic.face_data = face_data

            # 处理 detected_image（numpy 数组转为 ContentFile）
            detected_img = info.get('detected_image')
            if detected_img is not None:
                # numpy数组转为PNG字节流
                is_success, buffer = cv2.imencode(".png", detected_img)
                if is_success:
                    update_pic.detected_image.save(
                        f'detected_{update_pic.picture_id}.png',
                        ContentFile(buffer.tobytes())
                    )

            # 处理 relationship_image（BytesIO对象转为 ContentFile）
            relationship_img = info.get('relationship_image')
            if relationship_img is not None:
                relationship_img.seek(0)
                update_pic.relationship_image.save(
                    f'relationship_{update_pic.picture_id}.png',
                    ContentFile(relationship_img.read())
                )

            update_pic.save()
        return JsonResponse({'issue_id': issue.issue_id}, status=201)


class IssueSearch(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        POST接口：接收关键词字符串，在Issue的description、location和title字段中搜索，返回符合条件的事件ID列表，按匹配度排序
        """
        keywords = request.data.get('keywords')
        if not keywords:
            return JsonResponse({'error': 'Keywords are required'}, status=400)

        keyword_list = keywords.split()

        query = Q()
        for keyword in keyword_list:
            query |= Q(description__icontains=keyword)
            query |= Q(location__icontains=keyword)
            query |= Q(title__icontains=keyword)

        user_id = request.user.id if request.user.is_authenticated else None
        if user_id is None:
            return JsonResponse({'error': 'User not authenticated'}, status=401)

        matching_issues = Issue.objects.filter(query, author_id=user_id)

        if not matching_issues.exists():
            return JsonResponse({'error': 'No matching issues found'}, status=404)

        issue_match_scores = []
        for issue in matching_issues:
            match_count = sum(issue.description.lower().count(keyword.lower()) for keyword in keyword_list)
            issue_match_scores.append((issue.issue_id, match_count))

        sorted_issues = sorted(issue_match_scores, key=lambda x: x[1], reverse=True)
        sorted_issue_ids = [issue_id for issue_id, _ in sorted_issues]

        return JsonResponse({'matching_issue_ids': sorted_issue_ids}, status=200)


class PictureManagement(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET接口：接收图片ID，返回图片的详细属性，包括face_data
        """
        picture_id = request.query_params.get('picture_id')
        if not picture_id:
            return JsonResponse({'error': 'Picture ID is required'}, status=400)

        try:
            picture = Picture.objects.get(picture_id=picture_id)
        except Picture.DoesNotExist:
            return JsonResponse({'error': 'Picture not found'}, status=404)

        picture_data = {
            'picture_id': picture.picture_id,
            'issue_id': picture.issue.issue_id if picture.issue else None,
            'url': os.path.join(settings.MEDIA_URL, str(picture.url)),
            'upload_at': picture.upload_at.strftime('%Y-%m-%d %H:%M:%S') if picture.upload_at else None,
            'description': picture.description,
            'location': picture.location,
            'face_data': picture.face_data  # 添加face_data字段
        }
        return JsonResponse(picture_data, status=200)

    def post(self, request):
        """
        POST接口：接收图片ID和描述信息，更新图片的描述信息
        """
        picture_id = request.data.get('picture_id')
        description = request.data.get('description')

        if not picture_id or not description:
            return JsonResponse({'error': 'Picture ID and description are required'}, status=400)

        try:
            picture = Picture.objects.get(picture_id=picture_id)
            picture.description = description
            picture.save()
            return JsonResponse({'message': 'Description updated successfully'}, status=200)
        except Picture.DoesNotExist:
            return JsonResponse({'error': 'Picture not found'}, status=404)


class TextExpandView(APIView):
    """
    文本扩写API接口
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        POST接口：接收用户描述，返回扩写后的文本
        """
        try:
            description = request.data.get('description')

            if not description:
                return JsonResponse({'error': '描述内容不能为空'}, status=400)

            if not description.strip():
                return JsonResponse({'error': '描述内容不能为空'}, status=400)

            # 调用扩写函数
            expanded_text = expand_text(description.strip())

            return JsonResponse({
                'status': 'success',
                'original_text': description,
                'expanded_text': expanded_text
            }, status=200)

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'error': f'扩写失败：{str(e)}'
            }, status=500)


class ImageProxyView(APIView):
    """
    图片代理API，用于解决前端CORS问题
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET接口：代理获取图片文件
        """
        try:
            # 获取图片路径参数
            image_path = request.query_params.get('path')
            if not image_path:
                return JsonResponse({'error': '图片路径不能为空'}, status=400)

            # 构建完整的文件路径
            full_path = os.path.join(settings.MEDIA_ROOT, image_path)

            # 检查文件是否存在
            if not os.path.exists(full_path):
                raise Http404('图片文件不存在')

            # 检查文件是否在MEDIA_ROOT目录下（安全检查）
            if not os.path.abspath(full_path).startswith(os.path.abspath(settings.MEDIA_ROOT)):
                return JsonResponse({'error': '无效的文件路径'}, status=400)

            # 获取文件的MIME类型
            content_type, _ = mimetypes.guess_type(full_path)
            if not content_type:
                content_type = 'application/octet-stream'

            # 读取文件内容
            with open(full_path, 'rb') as f:
                file_data = f.read()

            # 返回文件内容
            response = HttpResponse(file_data, content_type=content_type)
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET'
            response['Access-Control-Allow-Headers'] = '*'

            return response

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'error': f'获取图片失败：{str(e)}'
            }, status=500)

