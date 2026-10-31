#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频生成异步任务模块
"""

import os
import json
import threading
import time
from django.conf import settings
from django.utils import timezone
from .models import Video, VideoPicture
from issue.models import Picture
from character_db.models import Character
from usermanage.models import User
from utils.edit import generate_conclusion, generate_video_from_json


class VideoGenerationTask:
    """视频生成任务类"""

    def __init__(self):
        self.active_tasks = {}  # 存储活跃的任务

    def start_video_generation(self, video_id, user_id, p_id_list, video_title, video_description,
                              use_digital_human=False, enable_smart_animation=True,
                              digital_human_source='existing', character_id=None, digital_human_avatar=None):
        """
        启动异步视频生成任务

        Args:
            video_id: 视频ID
            user_id: 用户ID
            p_id_list: 图片ID列表
            video_title: 视频标题
            video_description: 视频描述
            use_digital_human: 是否使用数字人开头
            enable_smart_animation: 是否开启图片智能动态化
            digital_human_source: 数字人头像来源 ('existing' 或 'upload')
            character_id: 角色ID（使用已有头像时）
            digital_human_avatar: 上传的头像文件路径（字符串）或文件对象
        """
        # 检查是否已有任务在运行
        if video_id in self.active_tasks:
            print(f"视频 {video_id} 已有任务在运行中")
            return False

        # 创建并启动线程
        thread = threading.Thread(
            target=self._generate_video_worker,
            args=(video_id, user_id, p_id_list, video_title, video_description,
                  use_digital_human, enable_smart_animation, digital_human_source,
                  character_id, digital_human_avatar),
            daemon=True
        )

        self.active_tasks[video_id] = {
            'thread': thread,
            'start_time': time.time(),
            'status': 'starting'
        }

        thread.start()
        print(f"视频生成任务已启动: {video_id}")
        return True

    def _generate_video_worker(self, video_id, user_id, p_id_list, video_title, video_description,
                              use_digital_human=False, enable_smart_animation=True,
                              digital_human_source='existing', character_id=None, digital_human_avatar=None):
        """
        视频生成工作线程
        """
        try:
            # 更新状态为处理中
            self._update_video_status(video_id, 'processing', 0, started_at=timezone.now())

            # 步骤1: 处理图片数据 (10%)
            self._update_progress(video_id, 10, "正在处理图片数据...")
            user_descriptions, pic_path, event_titles = self._process_pictures(p_id_list)

            # 步骤2: 获取用户角色信息 (20%)
            self._update_progress(video_id, 20, "正在获取用户信息...")
            protagonist = self._get_protagonist(user_id)

            # 步骤3: 生成文件路径 (30%)
            self._update_progress(video_id, 30, "正在准备文件...")
            video_file_name, video_output_path, script_output_path = self._prepare_file_paths(video_id, user_id)

            # 步骤4: 生成视频脚本 (50%)
            self._update_progress(video_id, 50, "正在生成视频脚本...")
            script = generate_conclusion(
                pic_path, user_descriptions, protagonist, script_output_path,
                use_digital_human, enable_smart_animation, digital_human_source,
                character_id, digital_human_avatar
            )

            # 步骤5: 生成视频 (90%)
            self._update_progress(video_id, 70, "正在生成视频，请耐心等待...")
            # generate_video_from_json函数期望脚本数据作为第一个参数
            generate_video_from_json(script, video_output_path)

            # 步骤6: 检查文件并更新数据库 (100%)
            self._update_progress(video_id, 90, "正在保存视频...")
            if not os.path.exists(video_output_path):
                raise Exception("视频文件生成失败")

            # 更新数据库记录
            self._update_video_record(
                video_id, video_title, video_description, event_titles,
                video_file_name, p_id_list
            )

            # 完成
            self._update_video_status(
                video_id, 'completed', 100,
                completed_at=timezone.now(),
                message="视频生成完成"
            )

            print(f"视频生成成功: {video_id}")

        except Exception as e:
            error_msg = f"视频生成失败: {str(e)}"
            print(error_msg)
            # 打印详细的错误信息用于调试
            import traceback
            traceback.print_exc()

            self._update_video_status(
                video_id, 'failed', 0,
                error_message=error_msg,
                completed_at=timezone.now()
            )

        finally:
            # 清理任务记录
            if video_id in self.active_tasks:
                del self.active_tasks[video_id]

    def _process_pictures(self, p_id_list):
        """处理图片数据"""
        user_descriptions = []
        pic_path = []
        k = 0
        issue_loc = {}
        event_titles = []

        for i in p_id_list:
            pic = Picture.objects.get(picture_id=i)
            if pic.issue.issue_id not in issue_loc:
                issue_loc[pic.issue.issue_id] = k
                k += 1
                pic_path.append([])
                user_descriptions.append(pic.issue.description)
                event_titles.append(pic.issue.title)

            # 修复路径问题：检查pic.url是否已经是完整路径
            pic_url_str = str(pic.url)
            if pic_url_str.startswith(settings.MEDIA_ROOT):
                # 如果已经是完整路径，直接使用
                image_path = pic_url_str
            else:
                # 如果是相对路径，才拼接MEDIA_ROOT
                image_path = os.path.join(settings.MEDIA_ROOT, pic_url_str)

            # 确保路径存在
            if not os.path.exists(image_path):
                print(f"警告：图片文件不存在: {image_path}")
                # 尝试相对路径
                alt_path = os.path.join(settings.MEDIA_ROOT, pic_url_str)
                if os.path.exists(alt_path):
                    image_path = alt_path
                    print(f"使用替代路径: {image_path}")

            j_pic = {
                'id': i,
                'original_image_path': image_path,
                'location': pic.location,
                'relations': pic.relations,
                'time': pic.upload_at.isoformat() if pic.upload_at else timezone.now().isoformat(),
                'description': pic.description,
            }
            pic_path[issue_loc[pic.issue.issue_id]].append(j_pic)

        return user_descriptions, pic_path, event_titles

    def _get_protagonist(self, user_id):
        """获取主角信息"""
        user = User.objects.get(id=user_id)
        try:
            character = Character.objects.get(belongs_to=user, relationship='自己')
        except Character.DoesNotExist:
            character = Character.objects.filter(belongs_to=user).first()
            if not character:
                raise Exception('用户角色信息不存在')

        # 修复头像路径问题
        avatar_path = ''
        if character.avatar:
            avatar_str = str(character.avatar)
            if avatar_str.startswith(settings.MEDIA_ROOT):
                avatar_path = avatar_str
            else:
                avatar_path = os.path.join(settings.MEDIA_ROOT, avatar_str)

        return {
            'name': character.name or user.username,
            'avatar': avatar_path,
            'gender': character.gender
        }

    def _prepare_file_paths(self, video_id, user_id):
        """准备文件路径"""
        video_file_name = f"video_{video_id}_{int(time.time())}"

        # 确保video目录存在
        video_dir = os.path.join(settings.MEDIA_ROOT, 'video')
        os.makedirs(video_dir, exist_ok=True)

        video_output_path = os.path.join(video_dir, video_file_name + '.mp4')
        script_output_path = os.path.join(video_dir, video_file_name + '_script.json')

        return video_file_name, video_output_path, script_output_path

    def _extract_events_from_pictures(self, p_id_list):
        """从图片数据中提取事件信息，构建JSON格式的事件数组（按Issue分组）"""
        events = []

        try:
            from issue.models import Picture

            # 获取图片信息，包含关联的issue
            pictures = Picture.objects.filter(picture_id__in=p_id_list).select_related('issue')

            # 按Issue分组，避免重复事件
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
                else:
                    # 如果图片没有关联的issue，单独处理
                    print(f"警告：图片 {picture.picture_id} 没有关联的事件")

            # 为每个Issue创建一个事件记录
            event_id = 1
            for issue_id, group in issue_groups.items():
                issue = group['issue']
                pictures_in_issue = group['pictures']

                # 使用Issue的信息
                event_title = issue.title or f"事件{event_id}"
                # 使用Issue的date字段，而不是图片的upload_at
                event_date = issue.date.strftime('%Y-%m-%d') if issue.date else '2025-01-01'

                # 构建事件数据
                event_data = {
                    'id': event_id,
                    'title': event_title,
                    'date': event_date
                }

                events.append(event_data)
                print(f"事件 {event_id}: {event_title} ({event_date}) - 包含 {len(pictures_in_issue)} 张图片")
                event_id += 1

            # 按事件日期排序
            events.sort(key=lambda x: x['date'])

            # 如果没有找到有效的事件，创建默认事件
            if not events:
                events = [{
                    'id': 1,
                    'title': '美好回忆',
                    'date': '2025-01-01'
                }]

            print(f"提取到 {len(events)} 个事件: {events}")
            return events

        except Exception as e:
            print(f"提取事件信息失败: {e}")
            import traceback
            traceback.print_exc()
            # 返回默认事件
            return [{
                'id': 1,
                'title': '美好回忆',
                'date': '2025-01-01'
            }]

    def _handle_db_connection_error(self, error, attempt, max_retries):
        """处理数据库连接错误的通用方法"""
        error_str = str(error).lower()
        connection_errors = [
            'mysql server has gone away',
            'interfaceerror',
            '2006',
            '(0, \'\')',
            'lost connection',
            'connection was killed',
            'can\'t connect to mysql server',
            'connection already closed',
            'connection timeout'
        ]

        if any(err in error_str for err in connection_errors) and attempt < max_retries - 1:
            try:
                from django.db import connection
                connection.close()
                print(f"检测到数据库连接错误: {error}")
                print("已关闭旧的数据库连接，准备重试...")
                import time
                # 指数退避重试：10s, 15s, 20s
                wait_time = 10 + (attempt * 5)
                print(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
                return True  # 表示应该重试
            except Exception as conn_err:
                print(f"关闭连接时出错: {conn_err}")
                time.sleep(15)
                return True
        return False  # 表示不应该重试

    def _ensure_db_connection(self):
        """确保数据库连接健康"""
        try:
            from django.db import connection
            connection.ensure_connection()
            # 执行一个简单的查询来测试连接
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except Exception as e:
            print(f"数据库连接检查失败: {e}")
            try:
                connection.close()
                print("已关闭异常的数据库连接")
            except:
                pass
            return False

    def _update_video_record(self, video_id, video_title, video_description, event_titles, video_file_name, p_id_list):
        """更新视频记录（带数据库重连机制）"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 预检查数据库连接
                if not self._ensure_db_connection():
                    print("数据库连接预检查失败，等待重试...")
                    import time
                    time.sleep(5)
                    continue

                video_obj = Video.objects.get(video_id=video_id)

                # 从图片数据中提取事件信息并构建JSON格式
                events_data = self._extract_events_from_pictures(p_id_list)

                # 更新视频信息
                video_obj.title = video_title
                video_obj.description = video_description
                video_obj.event_title = events_data  # 现在存储JSON数组
                video_obj.script_url = f"video/{video_file_name}_script.json"
                video_obj.video_url = f"video/{video_file_name}.mp4"
                video_obj.save()

                # 清除旧的图片关联
                VideoPicture.objects.filter(video=video_obj).delete()

                # 创建新的图片关联记录
                for pic_id in p_id_list:
                    VideoPicture.objects.create(
                        video=video_obj,
                        picture_id=pic_id
                    )

                print(f"视频记录更新成功: {video_id}")
                return True

            except Exception as e:
                print(f"更新视频记录失败 (尝试 {attempt + 1}/{max_retries}): {e}")

                # 使用通用的数据库连接错误处理方法
                if self._handle_db_connection_error(e, attempt, max_retries):
                    continue  # 重试
                else:
                    print(f"所有重试都失败，无法更新视频记录: {video_id}")
                    raise e  # 重新抛出异常，让上层处理

        return False

    def _update_video_status(self, video_id, status, progress=None, **kwargs):
        """更新视频状态（带数据库重连机制）"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 预检查数据库连接
                if not self._ensure_db_connection():
                    print("数据库连接预检查失败，等待重试...")
                    import time
                    time.sleep(5)
                    continue

                video = Video.objects.get(video_id=video_id)
                video.status = status
                if progress is not None:
                    video.progress = progress

                for key, value in kwargs.items():
                    if hasattr(video, key):
                        setattr(video, key, value)

                video.save()

                print(f"视频状态更新成功: {video_id} -> {status} ({progress}%)")
                return True

            except Video.DoesNotExist:
                print(f"视频不存在: {video_id}")
                return False

            except Exception as e:
                print(f"更新视频状态失败 (尝试 {attempt + 1}/{max_retries}): {e}")

                # 使用通用的数据库连接错误处理方法
                if self._handle_db_connection_error(e, attempt, max_retries):
                    continue  # 重试
                else:
                    print(f"所有重试都失败，无法更新视频状态: {video_id}")
                    return False

        return False

    def _update_progress(self, video_id, progress, message=""):
        """更新进度"""
        self._update_video_status(video_id, 'processing', progress)
        if message:
            print(f"视频 {video_id}: {progress}% - {message}")

    def get_task_status(self, video_id):
        """获取任务状态"""
        if video_id in self.active_tasks:
            task_info = self.active_tasks[video_id]
            return {
                'active': True,
                'running_time': time.time() - task_info['start_time'],
                'status': task_info['status']
            }
        return {'active': False}

    def cancel_task(self, video_id):
        """取消任务（注意：线程无法强制停止，只能标记为取消）"""
        if video_id in self.active_tasks:
            self._update_video_status(video_id, 'failed', error_message="任务已取消")
            del self.active_tasks[video_id]
            return True
        return False


# 全局任务管理器实例
video_task_manager = VideoGenerationTask()
