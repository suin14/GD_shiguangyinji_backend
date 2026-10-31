# coding=utf-8
import os
import pdb
import time
from http import HTTPStatus

import dashscope
import requests
from dashscope.audio.tts_v2 import *

import textwrap
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip

# 将your-dashscope-api-key替换成您自己的API-KEY
# dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')
dashscope.api_key = "sk-6aeae9bca1514876a495dd5c74b5ee90"
# api_key = os.getenv('DASHSCOPE_API_KEY')
api_key="sk-6aeae9bca1514876a495dd5c74b5ee90",
text = ("您好啊！我是张伟，刚泡了一壶茶，正好闲下来。不知道您愿不愿意和我一起聊聊天，"
        "分享一下您的故事？我特别喜欢听别人的人生经历，总能从中学到很多。")
gender = 'man'
audio_path = "output.mp3"
img_path = "./output/character.jpg"
img_prompt = "来自中国的年轻的男性采访者"
url = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/face-detect'
img_url_path = "https://gitee.com/lin-lingwww/resource/raw/master/image/character.jpg"
audio_url_path = "https://gitee.com/lin-lingwww/resource/raw/master/audio/output.mp3"
video_url = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/video-synthesis/'
video_path = "./output/old.mp4"
get_video_path = "./output/get_output.mp4"
new_video_path = "./output/new_output.mp4"


def generate_audio(audio_path, text, voice_flag):
    if voice_flag == "male":
        synthesizer = SpeechSynthesizer(model="cosyvoice-v1", voice="longshuo")
    elif voice_flag == "female":
        synthesizer = SpeechSynthesizer(model="cosyvoice-v1", voice="longyuan")
    else:
        print("voice flag error!")
        return
    audio = synthesizer.call(text)
    print('requestId: ', synthesizer.get_last_request_id())
    with open(audio_path, 'wb') as f:
        f.write(audio)


def generate_prompt(pt):
    n_message = [
        {
            "role": "system",
            "content": f"你是个专业的数字人生成的提示词写手，接受用户希望生成的数字人形象描述（可能包含改进建议），"
                       f"为数字人生成模型编写合适的提示词。"
                       f"生成的图像必须遵守的规范有：1、面部应该是主要焦点，占图像的 50%-70%；"
                       f"2、面部应面向前方，旋转角度小于 30°（无侧面轮廓）\n\n"
                       f"输出内容不要包含其他任何冗余信息。",
        },
        {
            "role": "user",
            "content": f"这是我想要的数字人形象：{pt}。"
        }
    ]
    return n_message


def generate_image(save_path, prompt, style):
    prompt_message = generate_prompt(prompt)
    response = dashscope.Generation.call(
        api_key=api_key,
        model="qwen-plus-2025-04-28",
        messages=prompt_message,
        result_format='message'
    )
    n_prompt = response["output"]["choices"][0]["message"].content
    rsp = dashscope.ImageSynthesis.call(
        api_key=api_key,
        model="wanx2.1-t2i-plus",
        prompt=n_prompt,
        n=1,
        style=style,
        size='1024*1024')
    print('response: %s' % rsp)
    if rsp.status_code == HTTPStatus.OK:
        with open(save_path, 'wb+') as f:
            f.write(requests.get(rsp.output.results[0].url).content)
    else:
        print('sync_call Failed, status_code: %s, code: %s, message: %s' %
              (rsp.status_code, rsp.code, rsp.message))


def generate_ref_image(save_path, prompt, style, sketch_image_url):
    prompt_message = generate_prompt(prompt)
    response = dashscope.Generation.call(
        api_key=api_key,
        model="qwen-plus-2025-04-28",
        messages=prompt_message,
        result_format='message'
    )
    n_prompt = response["output"]["choices"][0]["message"].content
    rsp = dashscope.ImageSynthesis.call(
        api_key=api_key,
        model="wanx2.1-t2i-plus",
        prompt=n_prompt,
        n=1,
        style=style,
        size='1024*1024',
        ref_mode='repaint',
        ref_strength=1.0,
        sketch_image_url=sketch_image_url)
    print('response: %s' % rsp)
    if rsp.status_code == HTTPStatus.OK:
        with open(save_path, 'wb+') as f:
            f.write(requests.get(rsp.output.results[0].url).content)
    else:
        print('sync_call Failed, status_code: %s, code: %s, message: %s' %
              (rsp.status_code, rsp.code, rsp.message))


def face_detect(img_url_path):
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    data = {
        "model": "emo-detect-v1",
        "input": {
            "image_url": img_url_path  # 替换为实际图片URL
        },
        "parameters": {
            "ratio": "3:4"
        }
    }

    response = requests.post(url, headers=headers, json=data)

    # 检查响应状态码和内容
    if response.status_code == 200:
        print('成功:', response.json())
    else:
        print('失败:', response.status_code, response.text)


def video_generate(img_url_path, audio_url_path):
    # 设置请求头部
    headers = {
        'X-DashScope-Async': 'enable',
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    # 设置请求体数据
    data = {
        "model": "emo-v1",
        "input": {
            "image_url": img_url_path,
            "audio_url": audio_url_path,
            "face_bbox": [359, 257, 641, 539],
            "ext_bbox": [129, 0, 871, 989]
        },
        "parameters": {
            "style_level": "normal"
        }
    }

    # 发送POST请求
    response = requests.post(video_url, headers=headers, json=data)

    # 检查响应状态码和内容
    if response.status_code == 200:
        print('成功:', response.json())
    else:
        print('失败:', response.status_code, response.text)


def character_detect(img_url_path):
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    data = {
        "model": "liveportrait-detect",
        "input": {
            "image_url": img_url_path  # 替换为实际图片URL
        }
    }

    response = requests.post(url, headers=headers, json=data)

    # 检查响应状态码和内容
    if response.status_code == 200:
        print('成功:', response.json())
        return response.json()['output']['pass']
    else:
        print('失败:', response.status_code, response.text)


def character_generate(img_url_path, audio_url_path):
    # 定义请求头
    headers = {
        'X-DashScope-Async': 'enable',
        'Authorization': f'Bearer {api_key}',  # 替换<YOUR_API_KEY>为你的实际API密钥
        'Content-Type': 'application/json'
    }

    # 定义请求数据
    data = {
        "model": "liveportrait",
        "input": {
            "image_url": img_url_path,
            "audio_url": audio_url_path,
        },
        "parameters": {
            "template_id": "normal",
             "eye_move_freq": 0.5,
             "video_fps": 30,
             "mouth_move_strength": 1,
             "paste_back": True,
             "head_move_strength": 0.5
        }
    }

    # 发送POST请求
    response = requests.post(video_url, headers=headers, json=data)

    # 检查响应
    if response.status_code == 200:
        print('请求成功，响应内容：', response.json())
        return response.json()['output']['task_id']
    else:
        print('请求失败，状态码：', response.status_code)


def get_task_status(task_id):
    url = f'https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}'

    # 设置请求头部
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    while True:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # 如果响应包含了一个HTTP错误状态码，则抛出异常

            # 打印或返回JSON格式的响应内容
            if (response.json()['output']['task_status'] == 'PENDING'
                    or response.json()['output']['task_status'] == 'RUNNING'):
                time.sleep(10)
                print('视频还未生成结束，任务状态:', response.json())
            elif response.json()['output']['task_status'] == 'SUCCEEDED':
                print('视频地址:', response.json()['output']['results']['video_url'])
                return response.json()['output']['results']['video_url']
            elif (response.json()['output']['task_status'] == 'FAILED'
                  or response.json()['output']['task_status'] == 'UNKNOWN'):
                print('视频生成失败，任务状态:', response.json())
                return None
        except requests.exceptions.RequestException as e:
            print(f"获取任务状态失败: {e}")
            return None


def download_video(video_url, output_path):
    # 设置一个合理的超时时间（秒）
    timeout = 10

    try:
        with requests.get(video_url, stream=True, timeout=timeout) as response:
            response.raise_for_status()  # 如果响应包含了一个HTTP错误状态码，则抛出异常
            with open(output_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:  # 过滤掉保持活动的None chunks
                        file.write(chunk)
        print(f"视频已成功下载到 {output_path}")
    except requests.exceptions.RequestException as e:
        print(f"下载失败: {e}")


def auto_wrap(text, width):
    return textwrap.fill(text, width)


def add_text(input_video_path, text, output_video_path):
    font_size = 36
    # 修复：调整横屏字幕换行参数，保持合理的字幕行数和速度
    ad_size = 0.0125  # 从 0.021875 调整为 0.0125，适配横屏显示
    video_clip = VideoFileClip(input_video_path)

    wrapped_text = auto_wrap(text, int(video_clip.size[0] * ad_size))

    # 创建文本剪辑
    text_clip = (TextClip(font='C:/Windows/Fonts/STXINGKA.TTF',
                          text=wrapped_text,
                          font_size=font_size,
                          color='white',
                          method='label',
                          size=(video_clip.size[0] - 400, None),
                          text_align='center',
                          horizontal_align='center',
                          duration=video_clip.duration)
                 .with_position(('center', 'bottom')))

    # 合成视频与文字
    final_clip = CompositeVideoClip([video_clip, text_clip])

    # 修复：添加完整的编码参数以支持进度条拖动
    final_clip.write_videofile(
        output_video_path,
        fps=video_clip.fps,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        ffmpeg_params=[
            "-movflags", "+faststart",
            "-pix_fmt", "yuv420p"
        ]
    )


if __name__ == '__main__':
    # generate_audio(audio_path, text, gender)

    # generate_image(img_path, img_prompt)

    # face_detect(img_url_path)

    # video_generate(img_url_path, audio_url_path)

    # character_detect(img_url_path)

    # character_generate(img_url_path, audio_url_path)


    get_task_status(task_id='5bce8bdd-21de-4605-9bfc-f0db3169d38f')


    # video_ali_url = ('http://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/1d/'
    #              '3f/20241219/149a0015/5bce8bdd-21de-4605-9bfc-f0db3169d38f.mp4?'
    #              'Expires=1734689511&OSSAccessKeyId=LTAI5tKPD3TMqf2Lna1fASuh&Sign'
    #              'ature=GxxOS3DhJiEmp%2F1JB9lprd5vihY%3D')
    #
    # download_video(video_ali_url, get_video_path)

    # add_text(get_video_path, text, new_video_path)
