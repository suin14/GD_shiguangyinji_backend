import pdb
from datetime import datetime
from http import HTTPStatus
from typing import Dict

import dashscope
from dashscope import MultiModalConversation
from moviepy import VideoFileClip

from .gvideo import generate_video, check_video_status
from .generate_pdf import create_pdf
from .handle import (handle_frame, adjust_audio_speed, add_audio, concat_videos,
                    add_text_dynamic, add_audio_text_dynamic, image_merge_video,
                    concat_video_clips)
from .generate_video import read_img, img2videos
from .ali import generate_sentence, get_title, repaint
from .ali_character import (generate_audio, generate_image, character_detect,
                           character_generate, get_task_status,
                           download_video, add_text, generate_ref_image)
import json
import requests
import base64

from PIL import Image
import os

from .detect_tools.detect import load_known_people, load_known_people_single, load_event

from dashscope import VideoSynthesis

from django.conf import settings

from pathlib import Path



def generate_json_file(data, output_json_path):
    with open(output_json_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)
    print(f"JSON文件已保存到 {output_json_path}")


def create_video_data():
    data = [
        {
            "image_path": "./resource/0.png",
            "is_character": True,
            "is_video": False,
            "video_prompt": "",
            "duration": 5,
            "text": "各位朋友，新年快到了！作为夕阳摄影交流群的一份子，我和群里的通伴们一起张罗了"
                    "一场特别热闹的迎春活动。我特别想跟大家分享一下当时那个欢乐的场景，"
                    "希望你们也能感受到我们的开心和兴奋！",
            "gender": "female"
        },
        {
            "image_path": "./resource/1.png",
            "is_character": False,
            "is_video": False,
            "video_prompt": "",
            "duration": 5,
            "text": "我和同伴们身穿红色服装在街头表演，手中挥舞着鲜艳的红绸带，鼓声在我们周围震天响动。"
                    "在表演中，我全身心地投入，与大家一起展现出对生活的热爱和节日的喜悦，这份激情感染了每一个围观的人。",
            "gender": "female"
        },
        {
            "image_path": "./resource/2.png",
            "is_character": False,
            "is_video": False,
            "video_prompt": "",
            "duration": 5,
            "text": "我们还进行了传统的舞龙表演，展示了成员技艺的精湛，也传递了我们对新年的美好"
                    "祝愿和对生活的热爱。看着这条栩栩如生的金龙，我感受到了一种浓浓的节日氛围和传统文化的魅力。",
            "gender": "female"
        }
    ]
    return data


def adjust_image(image_folder):
    for filename in os.listdir(image_folder):
        # 拼接文件路径
        file_path = os.path.join(image_folder, filename)

        # 确保是图片文件（根据扩展名判断）
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')):
            try:
                # 打开图片
                with Image.open(file_path) as img:
                    # 调整图片大小为 1920x1080
                    img_resized = img.resize((1920, 1080))

                    # 覆盖保存调整后的图片
                    img_resized.save(file_path)
                    print(f"图片 {filename} 已调整大小并保存。")
            except Exception as e:
                print(f"处理 {filename} 时发生错误: {e}")


# def upload_file(file_name, file_path_on_disk, max_retries=3):
#     """
#     上传文件到Gitee，后面得改
#     """
#     import time
#     import json

#     # 替换为你的实际信息
#     access_token = '4d48ac6d952d18e4fdb6cfae620739e2'
#     owner = 'lin-lingwww'
#     repo = 'resource'

#     # 读取文件内容
#     with open(file_path_on_disk, 'rb') as file:
#         content = file.read()

#     # 获取文件内容的Base64编码
#     content_base64 = base64.b64encode(content).decode('utf-8')

#     # API URL
#     url = f'https://gitee.com/api/v5/repos/{owner}/{repo}/contents/{file_name}'

#     # 重试机制
#     for attempt in range(max_retries):
#         try:
#             # 先检查文件是否已存在，获取SHA值
#             file_sha = None

#             # 获取文件信息
#             get_response = requests.get(url, params={'access_token': access_token}, timeout=10)

#             if get_response.status_code == 200:
#                 try:
#                     response_data = get_response.json()

#                     # 处理不同的响应格式
#                     if isinstance(response_data, list):
#                         # 如果返回的是列表，取第一个元素
#                         if len(response_data) > 0 and isinstance(response_data[0], dict):
#                             file_info = response_data[0]
#                             file_sha = file_info.get('sha')
#                             print(f"文件已存在（列表格式响应），将进行覆盖。SHA: {file_sha}")
#                         else:
#                             print("警告：API返回空列表或格式异常")
#                             if attempt < max_retries - 1:
#                                 print(f"第 {attempt + 1} 次尝试失败，等待重试...")
#                                 time.sleep(10)
#                                 continue
#                     elif isinstance(response_data, dict):
#                         # 正常的字典格式响应
#                         file_sha = response_data.get('sha')
#                         print(f"文件已存在，将进行覆盖。SHA: {file_sha}")
#                     else:
#                         print(f"警告：未知的响应格式: {type(response_data)}")
#                         if attempt < max_retries - 1:
#                             print(f"第 {attempt + 1} 次尝试失败，等待重试...")
#                             time.sleep(10)
#                             continue

#                 except json.JSONDecodeError as e:
#                     print(f"JSON解析错误: {e}")
#                     if attempt < max_retries - 1:
#                         print(f"第 {attempt + 1} 次尝试失败，等待重试...")
#                         time.sleep(10)
#                         continue

#             elif get_response.status_code == 404:
#                 print("文件不存在，将创建新文件")
#             else:
#                 print(f"检查文件状态时出错：{get_response.status_code}")
#                 if attempt < max_retries - 1:
#                     print(f"第 {attempt + 1} 次尝试失败，等待重试...")
#                     time.sleep(10)
#                     continue

#             # 构造请求数据
#             data = {
#                 'access_token': access_token,
#                 'message': 'Upload/Update file via Gitee API',
#                 'content': content_base64,
#                 'branch': 'master',
#             }

#             # 如果文件已存在，添加SHA值以进行覆盖
#             if file_sha:
#                 data['sha'] = file_sha

#             # 发送PUT请求（用于创建或更新文件）
#             response = requests.put(url, json=data, timeout=30)

#             if response.status_code in [200, 201]:  # 200 Updated, 201 Created
#                 action = "覆盖" if file_sha else "上传"
#                 print(f"文件{action}成功")

#                 # 返回文件的访问URL
#                 file_url = f"https://gitee.com/{owner}/{repo}/raw/master/{file_name}"
#                 return file_url
#             else:
#                 print(f"文件操作失败：{response.status_code}")
#                 try:
#                     error_info = response.json()
#                     print(f"错误详情：{error_info}")

#                     # 检查是否是SHA相关错误，如果是则重试
#                     if isinstance(error_info, dict) and 'messages' in error_info:
#                         messages = error_info['messages']
#                         if any('sha' in str(msg).lower() for msg in messages):
#                             if attempt < max_retries - 1:
#                                 print(f"SHA错误，第 {attempt + 1} 次尝试失败，等待重试...")
#                                 time.sleep(2)
#                                 continue
#                 except:
#                     print(f"响应内容：{response.text}")

#                 # 如果不是可重试的错误，或者已经是最后一次尝试，则返回None
#                 if attempt == max_retries - 1:
#                     return None
#                 else:
#                     print(f"第 {attempt + 1} 次尝试失败，等待重试...")
#                     time.sleep(2)
#                     continue

#         except requests.exceptions.RequestException as e:
#             print(f"网络请求异常: {e}")
#             if attempt < max_retries - 1:
#                 print(f"第 {attempt + 1} 次尝试失败，等待重试...")
#                 time.sleep(2)
#                 continue
#             else:
#                 return None
#         except Exception as e:
#             print(f"检查文件状态时发生异常：{e}")
#             if attempt < max_retries - 1:
#                 print(f"第 {attempt + 1} 次尝试失败，等待重试...")
#                 time.sleep(2)
#                 continue
#             else:
#                 return None

#     # 如果所有重试都失败了
#     print(f"经过 {max_retries} 次尝试后仍然失败")
#     return None


def get_upload_policy(api_key, model_name):
    """获取文件上传凭证"""
    url = "https://dashscope.aliyuncs.com/api/v1/uploads"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    params = {
        "action": "getPolicy",
        "model": model_name
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to get upload policy: {response.text}")
    
    return response.json()['data']

def upload_file_to_oss(policy_data, file_path):
    """将文件上传到临时存储OSS"""
    file_name = Path(file_path).name
    key = f"{policy_data['upload_dir']}/{file_name}"
    
    with open(file_path, 'rb') as file:
        files = {
            'OSSAccessKeyId': (None, policy_data['oss_access_key_id']),
            'Signature': (None, policy_data['signature']),
            'policy': (None, policy_data['policy']),
            'x-oss-object-acl': (None, policy_data['x_oss_object_acl']),
            'x-oss-forbid-overwrite': (None, policy_data['x_oss_forbid_overwrite']),
            'key': (None, key),
            'success_action_status': (None, '200'),
            'file': (file_name, file)
        }
        
        response = requests.post(policy_data['upload_host'], files=files)
        if response.status_code != 200:
            raise Exception(f"Failed to upload file: {response.text}")
    
    return f"oss://{key}"

def upload_file(api_key, model_name, file_path):
    """上传文件并获取URL"""
    # 1. 获取上传凭证，上传凭证接口有限流，超出限流将导致请求失败
    policy_data = get_upload_policy(api_key, model_name) 
    # 2. 上传文件到OSS
    oss_url = upload_file_to_oss(policy_data, file_path)
    
    return oss_url


# def generate_video_from_json(json_file_path, save_video_path):
#     # 读取JSON文件
#     with open(json_file_path, 'r', encoding='utf-8') as f:
#         data = json.load(f)
#
#     # 视频片段列表
#     video_clips = []
#
#     for i, item in enumerate(data):
#         image_path = item.get('image_path')
#         is_character = item.get('is_character', False)
#         is_video = item.get('is_video', False)
#         video_prompt = item.get('video_prompt', '')
#         duration = item.get('duration', 5)  # 默认持续时长5秒
#         text = item.get('text', '')
#         gender = item.get('gender', 'male')
#
#         # 如果需要生成数字人
#         if is_character:
#             tmp_audio_path = f"./tmp/edit_character{i}.mp3"
#             generate_audio(tmp_audio_path, text, gender)
#             image_url_name = f"image/edit_character{i}.jpg"
#             audio_url_name = f"audio/edit_character{i}.mp3"
#             upload_file(image_url_name, image_path)
#             upload_file(audio_url_name, tmp_audio_path)
#             image_url = f"https://gitee.com/lin-lingwww/resource/raw/master/{image_url_name}"
#             audio_url = f"https://gitee.com/lin-lingwww/resource/raw/master/{audio_url_name}"
#
#             if character_detect(image_url):
#             # if True:
#                 character_task_id = character_generate(image_url, audio_url)
#                 character_download_url = get_task_status(character_task_id)
#                 character_out_path = f"./character/edit_character{i}.mp4"
#                 download_video(character_download_url, character_out_path)
#                 original_video_clip = VideoFileClip(character_out_path)
#                 video_clip = add_text_dynamic(original_video_clip, text)
#                 video_clips.append(video_clip)
#             else:
#                 print("上传图片不适合生成数字人!")
#                 break
#         # 如果需要生成视频
#         elif is_video:
#             video_id = generate_video(image_path, video_prompt, duration=5)
#             video_url = check_video_status(video_id)
#             video_output_path = f"./video/edit_video{i}.mp4"
#             download_video(video_url, video_output_path)
#             tmp_audio_path = f"./tmp/edit_character{i}.mp3"
#             generate_audio(tmp_audio_path, text, gender)
#             video_clip = add_audio_text_dynamic(video_output_path, tmp_audio_path, text, i)
#             video_clips.append(video_clip)
#         # 如果只显示图片
#         else:
#             tmp_audio_path = f"./tmp/edit_character{i}.mp3"
#             if not os.path.exists(tmp_audio_path):
#                 generate_audio(tmp_audio_path, text, gender)
#             video_clip = image_merge_video(image_path, tmp_audio_path, text)
#             video_clips.append(video_clip)
#
#     # 合并所有视频片段成一个完整的视频
#     concat_video_clips(video_clips, save_video_path)
#
#     print(f'视频已生成并保存为 {save_video_path}')


def generate_video_from_json(json_file, save_video_path):
    # 读取JSON文件
    data = json_file

    # 视频片段列表
    video_clips = []

    # 创建临时目录（在循环外部定义，确保所有分支都能访问）
    tmp_dir = os.path.join(settings.MEDIA_ROOT, 'tmp')
    os.makedirs(tmp_dir, exist_ok=True)

    for i, item in enumerate(data):
        media_path = item.get('media_path')
        is_digital = item.get('is_digital')
        is_video = item.get('is_video')
        is_generate = item.get('generate_video')
        video_prompt = item.get('video_prompt', '')
        duration = item.get('duration', 5)  # 默认持续时长5秒
        content = item.get('content', '')
        short_content = item.get('short_content', '')
        gender = item.get('gender')
        avatar = item.get('digital')['avatar']

        # 根据是否生成视频选择使用的文本内容
        subtitle_text = short_content if is_generate else content

        # 如果需要生成数字人
        if is_digital:
            tmp_audio_path = os.path.join(tmp_dir, f"edit_character{i}.mp3")
            generate_audio(tmp_audio_path, item.get('digital')['introduction'], gender)
            image_url_name = f"image/edit_character{i}.jpg"
            audio_url_name = f"audio/edit_character{i}.mp3"

            # 上传文件并获取URL
            image_url = upload_file(image_url_name, avatar)
            audio_url = upload_file(audio_url_name, tmp_audio_path)

            # 检查上传是否成功
            if not image_url or not audio_url:
                print("文件上传失败，跳过数字人生成")
                continue

            if character_detect(image_url):
            # if True:
                character_task_id = character_generate(image_url, audio_url)
                character_download_url = get_task_status(character_task_id)
                character_dir = os.path.join(settings.MEDIA_ROOT, 'character')
                character_out_path = os.path.join(character_dir, f"edit_character{i}.mp4")
                download_video(character_download_url, character_out_path)
                original_video_clip = VideoFileClip(character_out_path)
                video_clip = add_text_dynamic(original_video_clip, item.get('digital')['introduction'])
                video_clips.append(video_clip)
            else:
                print("上传图片不适合生成数字人!")
                break
        # 如果需要生成视频
        elif is_generate:
            image_url_name = f"image/edit_image{i}.jpg"
            # image_url = upload_file(image_url_name, media_path)
            api_key="sk-6aeae9bca1514876a495dd5c74b5ee90"
            model="qwen-max-2025-01-25"
            image_url = upload_file(api_key, model, media_path)
            

            # 检查上传是否成功
            if not image_url:
                print("图片上传失败，跳过视频生成")
                continue
            video_url = image2video(image_url, video_prompt, duration)
            # 修复：将video文件夹设置在media目录下
            video_dir = os.path.join(settings.MEDIA_ROOT, 'video')
            os.makedirs(video_dir, exist_ok=True)
            video_output_path = os.path.join(video_dir, f"edit_video{i}.mp4")
            download_video(video_url, video_output_path)
            tmp_audio_path = os.path.join(tmp_dir, f"edit_character{i}.mp3")
            generate_audio(tmp_audio_path, subtitle_text, gender)
            video_clip = add_audio_text_dynamic(video_output_path, tmp_audio_path, subtitle_text, i)
            video_clips.append(video_clip)
        # 如果只显示图片
        else:
            tmp_audio_path = os.path.join(tmp_dir, f"edit_character{i}.mp3")
            generate_audio(tmp_audio_path, subtitle_text, gender)
            video_clip = image_merge_video(media_path, tmp_audio_path, subtitle_text)
            video_clips.append(video_clip)

    # 合并所有视频片段成一个完整的视频
    concat_video_clips(video_clips, save_video_path)

    print(f'视频已生成并保存为 {save_video_path}')


def generate_video_script(
        input_path: Dict,
        protagonist: Dict[str, str],
        enable_smart_animation: bool = True
):

    events = input_path

    sorted_events = sorted(
        events,
        key=lambda x: datetime.fromisoformat(str(x["time"])) if x.get("time") else datetime.min
    )

    output = []
    for count, event in enumerate(sorted_events):
        media_path = str(event["original_image_path"])
        is_video = media_path.lower().endswith(('.mp4', '.mov', '.avi'))

        # 生成提示词
        # prompt = f"{protagonist['name']}在{event['location']}，{event['description']}"
        # prompt += f"，时间：{event['time']}，环境：{event['location']}"

        prompt = "no"
        if not is_video and enable_smart_animation:
            prompt = judge_video(media_path, event['description'])

        content = generate_content(event['description'], event['location'],
                                   protagonist['name'], event['relations'])

        short_content = generate_short_content(event['description'], event['location'],
                                               protagonist['name'], event['relations'])

        # 构建输出项
        script_item = {
            "media_path": media_path,
            "is_video": is_video,
            "generate_video": False if prompt == "no" else True,
            "content": content,
            "short_content": short_content,
            "is_digital": False,
            "digital": {
                "introduction": "",
                "name": protagonist["name"],
                "avatar": protagonist["avatar"]
            },
            "duration": 5,
            "video_prompt": prompt,
            "extra_params": {
                "location": event["location"],
                "original_time": event["time"],
                "relation": event["relations"]
            },
            "gender": protagonist["gender"]
        }
        output.append(script_item)

    return output


def judge_video(img_path, description):
    # 修复路径重复拼接问题：检查img_path是否已经是完整路径
    if img_path.startswith(settings.MEDIA_ROOT):
        # 如果已经是完整路径，直接使用
        final_img_path = img_path.replace('\\','/')
    else:
        # 如果是相对路径，才拼接MEDIA_ROOT
        final_img_path = (settings.MEDIA_ROOT + '/' + img_path).replace('\\','/')

    print(f"judge_video 使用图片路径: {final_img_path}")

    # 检查文件是否存在
    if not os.path.exists(final_img_path):
        print(f"警告：图片文件不存在: {final_img_path}")
        return "no"
    messages = [{"role": "system",
             "content": [{"text": "你是AI视频生成专家。分析图片和描述，判断是否适合生成动态视频。\n\n"
                                  "【适合条件】\n"
                                  "1. 图片包含运动元素：人物动作、水流、云朵、车辆等\n"
                                  "2. 场景有延展性：风景、街道、活动现场等\n"
                                  "3. 描述有动态信息：动作词汇、时间变化等\n\n"
                                  "【不适合情况】\n"
                                  "静态物体特写、证件照、单一建筑物、纯文字图片\n\n"
                                  "【输出格式】\n"
                                  "适合：输出简洁的视频提示词（30字内）\n"
                                  "不适合：只输出'no'\n\n"
                                  "示例：\n"
                                  "输入：海边冲浪者准备下水\n"
                                  "输出：冲浪者跃入海浪，慢镜头展现水花四溅\n\n"
                                  "输入：一朵静止的花\n"
                                  "输出：no\n"
                                  "注意事项：输出no的时候不要包含其他任何信息"}]},
            {'role': 'user',
             'content': [{'image': final_img_path},
                         {'text': f"图片描述：{description}\n请判断是否适合生成视频"}]}]
    response = MultiModalConversation.call(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx"
        # api_key=os.getenv('DASHSCOPE_API_KEY'),
        api_key="sk-6aeae9bca1514876a495dd5c74b5ee90",
        model='qwen-vl-max-2025-04-08',
        messages=messages)

    # 健壮性检查
    try:
        return response["output"]["choices"][0]["message"].content[0]["text"]
    except Exception as e:
        print(f"judge_video API error: {e}, response: {response}")
        return "no"


def generate_content(description, location, protagonist, relations):
    messages = [
        {'role': 'system', 'content': '[角色定义]'
                                      '你是一位具备情感洞察力的社交媒体文案专家，擅长将视觉元素转化为有感染力的叙事表达。'
                                      '[核心任务]'
                                      '根据用户提供的以下四要素，以主人公第一人称视角撰写符合社交平台传播特性的经历分享：'
                                      '场景描述（包含视觉元素和氛围特征）'
                                      '地理位置信息（精确到具体坐标或标志性建筑）'
                                      '人物关系图谱（主人公身份+在场人员姓名及相对于主人公的关系）'
                                      '核心记忆点（未明确提供时需自行提炼）'
                                      '[处理规范]'
                                      '信息完整性校验：'
                                      '当人物关系缺失时，采用「模糊指代法」（如"几位老友"、"重要的伙伴"）'
                                      '主人公未明确时默认采用观察者视角，使用"我们"作为主体'
                                      '对矛盾信息采用「合理推测优先」原则'
                                      '[内容构建建议]'
                                      '用具象元素建立画面感（如"咖啡馆落地窗上的雨痕"）'
                                      '通过互动细节自然带出人物（如"表妹小雨执意要点的提拉米苏"）'
                                      '提炼引发共鸣的价值主张（如"原来幸福就是..."）'
                                      '[语言风格要求]'
                                      '口语化表达：使用聊天常用语态'
                                      '动态句式：考虑加入比喻或通感修辞'
                                      '情绪曲线：设置从场景描述到感悟升华的递进结构'
                                      '[注意事项]'
                                      '你的输出应该是一段主人公为第一人称的完整的话，且只包含经历分享内容，不含其他任何信息'},
        {'role': 'user', 'content': f'场景描述:{description},'
                                    f'地理位置信息:{location},'
                                    f'主人公姓名:{protagonist}'
                                    f'在场其他人员姓名及相对于主人公的关系:{relations}'}
    ]
    response = dashscope.Generation.call(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        # api_key=os.getenv('DASHSCOPE_API_KEY'),
        api_key="sk-6aeae9bca1514876a495dd5c74b5ee90",
        model="qwen-max-2025-01-25",
        messages=messages,
        result_format='message'
    )
    return response["output"]["choices"][0]["message"].content

def generate_short_content(description, location, protagonist, relations):
    messages = [
        {'role': 'system', 'content': '[角色定义]'
                                      '你是一位具备情感洞察力的社交媒体文案专家，擅长将视觉元素转化为有感染力的叙事表达。'
                                      '[核心任务]'
                                      '根据用户提供的以下四要素，以主人公第一人称视角撰写符合社交平台传播特性的经历分享：'
                                      '场景描述（包含视觉元素和氛围特征）'
                                      '地理位置信息（精确到具体坐标或标志性建筑）'
                                      '人物关系图谱（主人公身份+在场人员姓名及相对于主人公的关系）'
                                      '核心记忆点（未明确提供时需自行提炼）'
                                      '[处理规范]'
                                      '生成15个字左右（严格控制字数）'
                                      '你的输出应该是一段主人公为第一人称的完整的话，且只包含经历分享内容，不含其他任何信息'},
        {'role': 'user', 'content': f'场景描述:{description},'
                                    f'地理位置信息:{location},'
                                    f'主人公姓名:{protagonist}'
                                    f'在场其他人员姓名及相对于主人公的关系:{relations}'}
    ]
    response = dashscope.Generation.call(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        # api_key=os.getenv('DASHSCOPE_API_KEY'),
        api_key="sk-6aeae9bca1514876a495dd5c74b5ee90",
        model="qwen-max-2025-01-25",
        messages=messages,
        result_format='message'
    )
    return response["output"]["choices"][0]["message"].content


def generate_introduction(descriptions):
    messages = [
        {'role': 'system', 'content': '你是一位专业的开场白撰稿人，擅长以引人入胜的方式开启故事。'
                                      '用户提供即将在社交平台上分享的内容描述——通常包括多个旅行经历或难忘瞬间等。'
                                      '基于这些信息，请你为他们的故事创作一段富有吸引力、能够立即抓住读者注意力的开场白。'
                                      '[注意事项]'
                                      '这段开场白需要以第一人称视角撰写，'
                                      '并且尽可能要概括各个故事的核心亮点。'
                                      '你的输出应该只包含开场白，不含其他任何内容'},
        {'role': 'user', 'content': f'各个事件描述:{descriptions}'}
    ]
    print('messages: ', messages, type(messages))
    response = dashscope.Generation.call(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        # api_key=os.getenv('DASHSCOPE_API_KEY'),
        api_key="sk-6aeae9bca1514876a495dd5c74b5ee90",
        model="qwen-max-2025-01-25",
        messages=messages,
        result_format='message'
    )
    print('response: ', response, type(response))
    return response["output"]["choices"][0]["message"].content


def generate_conclusion(json_paths, descriptions, protagonist, output_path=None,
                       use_digital_human=False, enable_smart_animation=True,
                       digital_human_source='existing', character_id=None, digital_human_avatar=None):
    """
    生成视频脚本

    Args:
        json_paths: 事件数据列表
        descriptions: 事件描述列表
        protagonist: 主角信息
        output_path: 脚本输出路径（可选）
        use_digital_human: 是否使用数字人开头
        enable_smart_animation: 是否开启图片智能动态化
        digital_human_source: 数字人头像来源
        character_id: 角色ID
        digital_human_avatar: 上传的头像文件

    Returns:
        生成的脚本数据
    """
    descriptions = "||".join(descriptions)
    print('descriptions: ', descriptions, type(descriptions))

    output = []

    # 如果使用数字人开头，生成数字人脚本项
    if use_digital_human:
        introductions = generate_introduction(descriptions)

        # 处理数字人头像
        avatar_path = protagonist["avatar"]  # 默认使用主角头像
        if digital_human_source == 'existing' and character_id:
            # 使用已有角色头像
            try:
                from character_db.models import Character
                character = Character.objects.get(character_id=character_id)
                if character.avatar:
                    avatar_path = character.avatar.url
            except Exception as e:
                print(f"获取角色头像失败: {e}")
        elif digital_human_source == 'upload' and digital_human_avatar:
            # 使用上传的头像
            try:
                from django.conf import settings
                from django.core.files.storage import default_storage

                # 检查是否是文件路径（字符串）还是文件对象
                if isinstance(digital_human_avatar, str):
                    # 如果是文件路径，直接使用
                    if os.path.exists(digital_human_avatar):
                        # 将临时文件复制到正式存储位置
                        import time
                        import shutil
                        file_name = f"digital_human_{int(time.time())}_{os.path.basename(digital_human_avatar)}"
                        final_dir = os.path.join(settings.MEDIA_ROOT, 'digital_human')
                        os.makedirs(final_dir, exist_ok=True)
                        final_path = os.path.join(final_dir, file_name)
                        shutil.copy2(digital_human_avatar, final_path)
                        avatar_path = final_path

                        # 清理临时文件
                        try:
                            os.remove(digital_human_avatar)
                            print(f"已清理临时文件: {digital_human_avatar}")
                        except:
                            pass
                    else:
                        raise Exception(f"临时头像文件不存在: {digital_human_avatar}")
                else:
                    # 如果是文件对象，使用原来的逻辑
                    import time
                    file_name = f"digital_human_{int(time.time())}_{digital_human_avatar.name}"
                    file_path = default_storage.save(f"digital_human/{file_name}", digital_human_avatar)
                    avatar_path = default_storage.url(file_path)
            except Exception as e:
                print(f"保存上传头像失败: {e}")

        script_item = {
            "media_path": "",
            "is_video": False,
            "generate_video": False,
            "content": "",
            "short_content": "",
            "is_digital": True,
            "digital": {
                "introduction": introductions,
                "name": protagonist["name"],
                "avatar": avatar_path
            },
            "duration": 0,
            "video_prompt": "",
            "extra_params": {
                "location": "",
                "original_time": ""
            },
            "gender": protagonist["gender"]
        }
        output.append(script_item)

    for json_path in json_paths:
        output += generate_video_script(json_path, protagonist, enable_smart_animation)

    print('output: ', output)

    # 如果提供了输出路径，保存脚本文件
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f'脚本已保存到: {output_path}')

    return output


def image2video(img_url, video_prompt, duration):
    # call sync api, will return the result
    print('开始生成视频...')
    rsp = VideoSynthesis.call(model='wanx2.1-i2v-plus',
                              prompt=video_prompt,
                              img_url=img_url)
    # print(rsp)
    if rsp.status_code == HTTPStatus.OK:
        return rsp.output.video_url
    else:
        print('Failed, status_code: %s, code: %s, message: %s' %
              (rsp.status_code, rsp.code, rsp.message))

def expand_text(description):
    """
    扩写用户描述，生成更丰富的时光片段描述

    Args:
        description: 用户原始描述

    Returns:
        扩写后的描述文本
    """
    messages = [
        {'role': 'system', 'content': '[角色定义]\n'
                                      '你是一位专业的时光记录文案师，擅长将简短的生活片段扩写成富有情感和画面感的美好回忆。\n\n'
                                      '[核心任务]\n'
                                      '将用户提供的简短描述扩写成200-300字的精美文案，适合在时光记录应用中保存和分享。\n\n'
                                      '[扩写原则]\n'
                                      '1. 保持原意不变：忠实于用户的原始表达和情感\n'
                                      '2. 增强画面感：添加具体的视觉、听觉、触觉等感官细节\n'
                                      '3. 丰富情感层次：深化情感表达，让回忆更加动人\n'
                                      '4. 优化语言表达：使用优美、流畅的语言，提升文字质感\n'
                                      '5. 增加时光感：体现时间的珍贵和回忆的美好\n\n'
                                      '[写作技巧]\n'
                                      '- 运用细节描写：如"阳光透过树叶洒下斑驳的光影"\n'
                                      '- 融入感官体验：如"微风带来淡淡花香"\n'
                                      '- 表达内心感受：如"那一刻，时间仿佛静止了"\n'
                                      '- 使用比喻修辞：让描述更加生动形象\n'
                                      '- 营造氛围感：通过环境描写烘托情感\n\n'
                                      '[注意事项]\n'
                                      '- 保持第一人称视角，贴近用户的真实感受\n'
                                      '- 语言风格温暖、真诚，适合个人回忆记录\n'
                                      '- 避免过度夸张，保持真实感和可信度\n'
                                      '- 字数控制在200-300字之间\n'
                                      '- 只输出扩写后的文案，不包含其他内容'},
        {'role': 'user', 'content': f'请帮我扩写这段时光片段的描述：{description}'}
        ]
    response = dashscope.Generation.call(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        # api_key=os.getenv('DASHSCOPE_API_KEY'),
        api_key="sk-6aeae9bca1514876a495dd5c74b5ee90",
        model="qwen-max-2025-01-25",
        messages=messages,
        result_format='message'
        )
    return response["output"]["choices"][0]["message"].content



if __name__ == '__main__':
    output_json_path = "output_video_data.json"
    output_video_path = "./output/final_video.mp4"

    # file_name = 'image/test_character.jpg'  # 目标文件夹路径及文件名
    # file_path_on_disk = '../output/character.jpg'  # 本地文件路径
    # upload_file(file_name, file_path_on_disk)

    # imgs = ["./resource/1.png", "./resource/2.png"]
    # count = 2
    # response_list, t_content = generate_sentence(imgs, count)

    # video_data = create_video_data()
    # generate_json_file(video_data, output_json_path)

    # adjust_image("./resource")

    # 事件一:用户上传一个事件锚点，进行人物标注、关系图绘制和描述生成
    # 寻找数据逻辑(用户数据)
    user_path = "./resource/user.json"
    user_id = 1
    with open(user_path, 'r', encoding='utf-8') as f:
        users = json.load(f)
    protagonist = None
    for item in users:
        if item.get("user_id") == user_id:
            protagonist = item
            break

    # # 寻找数据逻辑(用户相关人物数据)
    # character_path = "./resource/detect_face.json"
    # with open(character_path, 'r', encoding='utf-8') as f:
    #     characters = json.load(f)
    #
    # # 这里将人脸识别数据也存进表里，以后不用再次识别了
    # for item in characters:
    #     if item.get("belongs_to") == user_id:
    #         if "known_encodings" not in item or item["known_encodings"] is None:
    #             item["known_encodings"] = load_known_people_single(item).tolist()
    # with open(character_path, 'w', encoding='utf-8') as f:
    #     json.dump(characters, f, ensure_ascii=False, indent=4)
    #
    # user_characters = [item for item in characters if item.get("belongs_to") == 1]
    #
    # # 上传事件数据(用户描述+照片列表+事件时间)
    # user_description = "我和一家人去西湖游玩时拍摄了一系列旅游照"  # 用来帮助检索地点和文案生成，由用户提供
    # user_time = "2024-07-15 14:30"  # 这个不清楚要不要设置给每张照片
    # event_id = 1  # 这个需要你给事件设置一下
    # target_path = "./resource/target_face.json"
    # with open(target_path, 'r', encoding='utf-8') as f:
    #     targets = json.load(f)
    # event = [target["image_path"] for target in targets]
    #
    # # 照片和描述保存地址
    # photo_path = "./output/images"
    # output_path = "./output/test_output.json"
    #
    # # 调用函数
    # load_event(protagonist, user_characters, user_description, user_time, event, event_id, photo_path, output_path)

    # generate_video_from_json(output_json_path, output_video_path)

    # 事件二:用户上传多个事件锚点，进行视频脚本文件的生成
    # 输入:视频脚本文件保存地址script_output_path,
    # 列表的列表(其中每个列表是某一个事件下选的一系列照片的信息，这里用json文件模拟),整个事件的描述列表
    script_output_path = "./output/script_output.json"
    json_paths = ["./output/test_output.json"]
    user_descriptions = ["我和一家人去西湖游玩时拍摄了一系列旅游照"]
    # generate_conclusion(json_paths, user_descriptions, protagonist, script_output_path)

    # 事件三:根据视频脚本文件，生成最终的视频
    video_output_path = "./output/final_generate.mp4"
    generate_video_from_json(script_output_path, video_output_path)
