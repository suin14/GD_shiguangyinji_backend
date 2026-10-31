from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Character
import json
from datetime import datetime
from utils.permissions import IsOwner
from rest_framework.permissions import IsAuthenticated
import os
from django.conf import settings
from utils.detect_tools.detect import load_known_people_single


class CharacterView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, character_id=None):
        """
        获取人物列表或单个详情
        """
        if character_id:
            try:
                character = Character.objects.get(
                    character_id=character_id, belongs_to=request.user
                )
                data = {
                    "character_id": character.character_id,
                    "name": character.name,
                    "gender": character.gender,
                    "relationship": character.relationship,
                    "birthday": (
                        character.birthday.strftime("%Y-%m-%d")
                        if character.birthday
                        else None
                    ),
                    "avatar": (
                        request.build_absolute_uri(character.avatar.url)
                        if character.avatar
                        else None
                    ),
                    "has_face_data": bool(character.face_data),  # 添加face_data状态
                    "face_data_length": len(character.face_data) if character.face_data else 0,  # 调试信息
                }
                return JsonResponse({"status": "success", "data": data})
            except Character.DoesNotExist:
                return JsonResponse(
                    {"status": "error", "message": "人物不存在"}, status=404
                )
        else:
            characters = Character.objects.filter(belongs_to=request.user)
            data = [
                {
                    "character_id": c.character_id,
                    "name": c.name,
                    "gender": c.gender,
                    "relationship": c.relationship,
                    "birthday": c.birthday.strftime("%Y-%m-%d") if c.birthday else None,
                    "avatar": (
                        request.build_absolute_uri(c.avatar.url) if c.avatar else None
                    ),
                }
                for c in characters
            ]
            return JsonResponse({"status": "success", "data": data})

    def post(self, request):
        """
        创建新人物
        """
        try:
            data = request.POST

            # 验证必填字段
            if not data.get("name"):
                return JsonResponse({"status": "error", "message": "姓名为必填项"}, status=400)
            if not data.get("relationship"):
                return JsonResponse({"status": "error", "message": "关系为必填项"}, status=400)
            if "avatar" not in request.FILES:
                return JsonResponse({"status": "error", "message": "头像为必填项"}, status=400)

            character = Character.objects.create(
                name=data.get("name"),
                gender=data.get("gender", "male"),
                relationship=data.get("relationship"),
                birthday=(
                    datetime.strptime(data.get("birthday"), "%Y-%m-%d").date()
                    if data.get("birthday")
                    else None
                ),
                belongs_to=request.user,
                avatar=request.FILES["avatar"]
            )

            # 调用人脸检测
            if character.avatar:
                try:
                    from utils.detect_tools.detect import load_known_people_single
                    import os
                    from django.conf import settings

                    # 构建avatar的完整路径
                    avatar_path = os.path.join(settings.MEDIA_ROOT, str(character.avatar))
                    print(f"开始为新角色 {character.name} 进行人脸检测，图片路径: {avatar_path}")

                    # 检查文件是否存在
                    if not os.path.exists(avatar_path):
                        print(f"错误：头像文件不存在: {avatar_path}")
                        character.delete()  # 删除已创建的character记录
                        return JsonResponse({"status": "error", "message": "头像文件不存在"}, status=400)

                    # 调用人脸检测
                    face_encoding = load_known_people_single({'avatar': avatar_path})

                    if face_encoding is not None:
                        # 将numpy数组转换为列表以便存储
                        character.face_data = face_encoding.tolist()
                        character.save()
                        print(f"成功为新角色 {character.name} 生成人脸数据，数据长度: {len(character.face_data)}")
                    else:
                        print(f"警告：未能为新角色 {character.name} 生成人脸数据")

                except Exception as e:
                    print(f"人脸检测失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    # 不影响主要的保存流程

            return JsonResponse(
                {
                    "status": "success",
                    "message": "创建成功",
                    "character_id": character.character_id,
                },
                status=201,
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    def put(self, request, character_id):
        """
        更新人物信息
        """
        try:
            character = Character.objects.get(
                character_id=character_id, belongs_to=request.user
            )
            data = request.POST
            avatar_changed = False

            if "name" in data:
                character.name = data["name"]
            if "gender" in data:
                character.gender = data["gender"]
            if "relationship" in data:
                character.relationship = data["relationship"]
            if "birthday" in data:
                character.birthday = datetime.strptime(
                    data["birthday"], "%Y-%m-%d"
                ).date()
            if "avatar" in request.FILES:
                character.avatar = request.FILES["avatar"]
                avatar_changed = True

            character.save()

            # 如果avatar改动，调用人脸检测
            if avatar_changed and character.avatar:
                try:
                    from utils.detect_tools.detect import load_known_people_single
                    import os
                    from django.conf import settings

                    # 构建avatar的完整路径
                    avatar_path = os.path.join(settings.MEDIA_ROOT, str(character.avatar))
                    print(f"开始为角色 {character.name} 进行人脸检测，图片路径: {avatar_path}")

                    # 检查文件是否存在
                    if not os.path.exists(avatar_path):
                        print(f"错误：头像文件不存在: {avatar_path}")
                        return JsonResponse({"status": "error", "message": "头像文件不存在"}, status=400)

                    # 调用人脸检测
                    face_encoding = load_known_people_single({'avatar': avatar_path})

                    if face_encoding is not None:
                        # 将numpy数组转换为列表以便存储
                        character.face_data = face_encoding.tolist()
                        character.save()
                        print(f"成功为角色 {character.name} 生成人脸数据，数据长度: {len(character.face_data)}")
                    else:
                        print(f"警告：未能为角色 {character.name} 生成人脸数据")

                except Exception as e:
                    print(f"人脸检测失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    # 不影响主要的保存流程

            return JsonResponse({"status": "success", "message": "更新成功"})
        except Character.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "人物不存在"}, status=404
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    def delete(self, request, character_id):
        """
        删除人物
        """
        try:
            character = Character.objects.get(
                character_id=character_id, belongs_to=request.user
            )
            character.delete()
            return JsonResponse({"status": "success", "message": "删除成功"})
        except Character.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "人物不存在"}, status=404
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    def get_queryset(self):
        """
        搜索人物
        """
        name = self.request.GET.get("name", "")
        characters = Character.objects.filter(
            belongs_to=self.request.user, name__icontains=name
        )
        data = [
            {
                "character_id": c.character_id,
                "name": c.name,
                "gender": c.gender,
                "relationship": c.relationship,
                "birthday": c.birthday.strftime("%Y-%m-%d") if c.birthday else None,
                "avatar": (
                    self.request.build_absolute_uri(c.avatar.url) if c.avatar else None
                ),
            }
            for c in characters
        ]
        return JsonResponse({"status": "success", "data": data})


class UserCharacterView(APIView):
    """
    用户角色信息管理 - 专门处理用户自己的角色信息
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        """
        获取用户自己的角色信息
        """
        try:
            character = Character.objects.get(
                belongs_to=request.user,
                relationship='自己'
            )
            data = {
                "character_id": character.character_id,
                "name": character.name,
                "gender": character.gender,
                "birthday": (
                    character.birthday.strftime("%Y-%m-%d")
                    if character.birthday
                    else None
                ),
                "avatar": (
                    request.build_absolute_uri(character.avatar.url)
                    if character.avatar
                    else None
                ),
                "has_face_data": bool(character.face_data)
            }
            return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)
        except Character.DoesNotExist:
            return Response(
                {"status": "error", "message": "用户角色信息不存在"},
                status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request):
        """
        创建用户自己的角色信息
        """
        try:
            # 检查是否已存在用户角色信息
            existing_character = Character.objects.filter(
                belongs_to=request.user,
                relationship='自己'
            ).first()

            if existing_character:
                return Response(
                    {"status": "error", "message": "用户角色信息已存在，请使用更新接口"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 获取表单数据
            name = request.data.get('name')
            gender = request.data.get('gender')
            birthday = request.data.get('birthday')
            avatar = request.FILES.get('avatar')

            # 验证必填字段
            if not name:
                return Response(
                    {"status": "error", "message": "真实姓名为必填项"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not gender:
                return Response(
                    {"status": "error", "message": "性别为必填项"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not avatar:
                return Response(
                    {"status": "error", "message": "真人头像为必填项"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 创建角色记录
            character = Character.objects.create(
                name=name,
                gender=gender,
                relationship='自己',
                birthday=(
                    datetime.strptime(birthday, "%Y-%m-%d").date()
                    if birthday
                    else None
                ),
                belongs_to=request.user,
                avatar=avatar
            )

            # 进行人脸检测并保存face_data
            try:
                avatar_path = os.path.join(settings.MEDIA_ROOT, str(character.avatar))
                face_encoding = load_known_people_single({'avatar': avatar_path})

                if face_encoding is not None:
                    # 将numpy数组转换为列表以便存储
                    character.face_data = face_encoding.tolist()
                    character.save()

                    return Response({
                        "status": "success",
                        "message": "用户角色信息创建成功，人脸数据已提取",
                        "character_id": character.character_id,
                        "has_face_data": True
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response({
                        "status": "warning",
                        "message": "用户角色信息创建成功，但未能提取人脸数据，请确保头像中包含清晰的人脸",
                        "character_id": character.character_id,
                        "has_face_data": False
                    }, status=status.HTTP_201_CREATED)

            except Exception as face_error:
                print(f"人脸检测错误: {face_error}")
                return Response({
                    "status": "warning",
                    "message": f"用户角色信息创建成功，但人脸检测失败: {str(face_error)}",
                    "character_id": character.character_id,
                    "has_face_data": False
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"status": "error", "message": f"创建失败: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def put(self, request):
        """
        更新用户自己的角色信息
        """
        try:
            character = Character.objects.get(
                belongs_to=request.user,
                relationship='自己'
            )

            # 获取表单数据
            name = request.data.get('name')
            gender = request.data.get('gender')
            birthday = request.data.get('birthday')
            avatar = request.FILES.get('avatar')

            # 更新字段
            if name:
                character.name = name
            if gender:
                character.gender = gender
            if birthday:
                character.birthday = datetime.strptime(birthday, "%Y-%m-%d").date()

            # 如果上传了新头像，需要重新进行人脸检测
            if avatar:
                character.avatar = avatar
                character.save()  # 先保存文件

                try:
                    avatar_path = os.path.join(settings.MEDIA_ROOT, str(character.avatar))
                    face_encoding = load_known_people_single({'avatar': avatar_path})

                    if face_encoding is not None:
                        character.face_data = face_encoding.tolist()
                        character.save()

                        return Response({
                            "status": "success",
                            "message": "用户角色信息更新成功，人脸数据已更新",
                            "has_face_data": True
                        }, status=status.HTTP_200_OK)
                    else:
                        character.face_data = None
                        character.save()
                        return Response({
                            "status": "warning",
                            "message": "用户角色信息更新成功，但未能提取人脸数据",
                            "has_face_data": False
                        }, status=status.HTTP_200_OK)

                except Exception as face_error:
                    print(f"人脸检测错误: {face_error}")
                    character.face_data = None
                    character.save()
                    return Response({
                        "status": "warning",
                        "message": f"用户角色信息更新成功，但人脸检测失败: {str(face_error)}",
                        "has_face_data": False
                    }, status=status.HTTP_200_OK)
            else:
                character.save()
                return Response({
                    "status": "success",
                    "message": "用户角色信息更新成功",
                    "has_face_data": bool(character.face_data)
                }, status=status.HTTP_200_OK)

        except Character.DoesNotExist:
            return Response(
                {"status": "error", "message": "用户角色信息不存在"},
                status=status.HTTP_404_NOT_FOUND
            )