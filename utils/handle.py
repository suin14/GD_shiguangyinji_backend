import os
import pdb
import subprocess
import textwrap

import numpy as np
from moviepy import VideoFileClip, concatenate_videoclips, ImageSequenceClip, AudioFileClip, TextClip, \
    CompositeVideoClip, ImageClip, VideoClip

from .ali_character import generate_audio, add_text

import shutil, os


text = "坐在草地上，感受田野的芬芳，我感觉大自然是如此的美好"


def handle_frame(input_path, output_path):
    video_clip = VideoFileClip(input_path)
    valid_frames = []
    for i, frame in enumerate(video_clip.iter_frames(fps=video_clip.fps, dtype="uint8")):
        try:
            # 检查帧是否有效 (例如：是否全为 0，表示损坏帧)
            if np.sum(frame) == 0:
                print(f"跳过无效帧: {i}")
                continue

            valid_frames.append(frame)
        except Exception as e:
            print(f"读取帧 {i} 发生错误，跳过: {e}")
            continue

    # 合并所有有效片段
    end_clip = ImageSequenceClip(valid_frames, fps=video_clip.fps)

    # 修复：添加完整的编码参数以支持进度条拖动
    end_clip.write_videofile(
        output_path,
        codec="libx264",
        preset="medium",
        ffmpeg_params=[
            "-movflags", "+faststart",
            "-pix_fmt", "yuv420p"
        ]
    )


def add_audio(input_path, audio_path, output_path):
    video_clip = VideoFileClip(input_path)
    audio_clip = AudioFileClip(audio_path)

    # 截取音频，不超出其原始长度
    audio_clip = audio_clip.subclipped(0, min(video_clip.duration, audio_clip.duration))

    # 设置音频到视频
    video_with_audio = video_clip.with_audio(audio_clip)

    # 修复：添加完整的编码参数以支持进度条拖动
    video_with_audio.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        ffmpeg_params=[
            "-movflags", "+faststart",
            "-pix_fmt", "yuv420p"
        ]
    )


def adjust_audio_speed(input_path, video_path, output_path):
    video_clip = VideoFileClip(video_path)
    audio_clip = AudioFileClip(input_path)

    video_duration = video_clip.duration
    audio_duration = audio_clip.duration
    speed_factor = audio_duration / video_duration

    if speed_factor < 0.5:
        speed_factor = 0.5
    elif speed_factor > 2:
        speed_factor = 2

    ffmpeg_command = [
        "ffmpeg",
        "-i", input_path,
        "-filter:a", f"atempo={speed_factor}",
        output_path
    ]
    
    # print("which ffmpeg:", shutil.which("ffmpeg"))
    # print("PATH:", os.environ.get("PATH"))
    
    # print(f"ffmpeg: {ffmpeg_command}")
    # print(f"输入音频: {input_path}")
    # print(f"输入视频: {video_path}")
    # print(f"输出音频: {output_path}")
        
    # print(f"输入音频存在: {os.path.exists(input_path)}")
    # print(f"输入视频存在: {os.path.exists(video_path)}")
    # print(f"输出目录存在: {os.path.exists(output_path)}")
    
    # 调用 FFmpeg 命令
    subprocess.run(ffmpeg_command, check=True)
    print(f"音频已成功调整语速，保存为: {output_path}")


def concat_videos(video_files, output_path):
    # 加载所有视频剪辑
    video_clips = [VideoFileClip(video).resized((1920, 1080)) for video in video_files]

    # 将视频拼接在一起
    final_video = concatenate_videoclips(video_clips, method="compose")

    # 修复：添加完整的编码参数以支持进度条拖动
    final_video.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        ffmpeg_params=[
            "-movflags", "+faststart",
            "-pix_fmt", "yuv420p"
        ]
    )


def concat_video_clips(video_clips, output_path):
    """
    拼接视频片段（使用MoviePy）
    """
    print(f"正在拼接 {len(video_clips)} 个视频片段...")

    # 直接使用MoviePy进行视频拼接
    final_video = concatenate_videoclips(video_clips, method="compose")

    # 修复：添加完整的编码参数以支持进度条拖动
    final_video.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        preset="medium",  # 平衡编码速度和质量
        ffmpeg_params=[
            "-movflags", "+faststart",  # 将moov原子移到文件开头，支持流媒体播放
            "-pix_fmt", "yuv420p"       # 确保兼容性
        ]
    )

    print("✅ 视频拼接完成")


def auto_wrap(text, width):
    return textwrap.fill(text, width)


def add_text_dynamic(video_clip, text):
    """
    为视频添加动态字幕（兼容性优化版本）
    """
    if not text or not text.strip():
        return video_clip

    font_size = 36
    # 修复：调整横屏字幕换行参数，保持合理的字幕行数和速度
    # 横屏时减少每行字符数，保持字幕节奏与语音同步
    ad_size = 0.0125  # 从 0.021875 调整为 0.0125，适配横屏显示

    video_clip = video_clip.resized((1920, 1080))

    # 计算字幕框的宽度
    wrapped_text = auto_wrap(text, int(video_clip.size[0] * ad_size))

    # 将每一行分开，按句子或自定义分行
    lines = wrapped_text.split("\n")

    # 检查音频是否存在
    if not hasattr(video_clip, 'audio') or video_clip.audio is None:
        print("⚠️  视频没有音频，使用默认时长")
        audio_duration = max(5.0, len(lines) * 2.0)  # 默认每行2秒
    else:
        audio_duration = video_clip.audio.duration

    # 每行字幕显示的时间
    line_duration = audio_duration / len(lines) if len(lines) > 0 else audio_duration

    # 获取可用的字体路径
    def get_available_font():
        """获取可用的中文字体"""
        font_paths = [
            'C:/Windows/Fonts/simhei.ttf',      # 黑体
            'C:/Windows/Fonts/simsun.ttc',      # 宋体
            'C:/Windows/Fonts/STXINGKA.TTF',    # 华文行楷
            'C:/Windows/Fonts/msyh.ttc',        # 微软雅黑
            '/System/Library/Fonts/PingFang.ttc',  # macOS
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # Linux
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                return font_path

        print("⚠️  未找到中文字体，使用默认字体")
        return None

    # 创建字幕剪辑
    text_clips = []
    font_path = get_available_font()

    for i, line in enumerate(lines):
        if not line.strip():
            continue

        try:
            # 创建文本剪辑参数
            text_params = {
                'text': line.strip(),
                'font_size': font_size,
                'color': 'white',
                'duration': line_duration
            }

            # 如果有字体文件，添加字体参数
            if font_path:
                text_params['font'] = font_path

            # 尝试创建TextClip（兼容不同版本的参数）
            try:
                text_clip = TextClip(
                    method='label',
                    size=(video_clip.size[0] - 400, None),
                    **text_params
                ).with_position(('center', video_clip.size[1] - 120)).with_start(i * line_duration)
            except TypeError:
                # 如果参数不兼容，使用简化版本
                text_clip = TextClip(
                    **text_params
                ).with_position(('center', 'bottom')).with_start(i * line_duration)

            text_clips.append(text_clip)

        except Exception as e:
            print(f"⚠️  创建字幕失败: {e}，跳过该行字幕")
            continue

    # 如果没有成功创建任何字幕，返回原视频
    if not text_clips:
        print("⚠️  未能创建字幕，返回原视频")
        return video_clip

    try:
        # 合成视频与文字
        final_clip = CompositeVideoClip([video_clip] + text_clips)
        return final_clip
    except Exception as e:
        print(f"⚠️  合成字幕失败: {e}，返回原视频")
        return video_clip


def add_audio_text_dynamic(input_video_path, audio_path, text, i):
    """
    为视频添加音频和字幕（使用MoviePy）
    """
    print("使用MoviePy进行视频处理...")
    from django.conf import settings

    # 创建临时目录
    tmp_dir = os.path.join(settings.MEDIA_ROOT, 'tmp')
    os.makedirs(tmp_dir, exist_ok=True)

    # 调整音频速度
    tmp_audio_path = os.path.join(tmp_dir, f"adjust_audio{i}.mp3")
    adjust_audio_speed(audio_path, input_video_path, tmp_audio_path)

    # 加载视频和音频
    video_clip = VideoFileClip(input_video_path)
    video_clip = video_clip.resized((1920, 1080))
    audio_clip = AudioFileClip(tmp_audio_path)

    # 截取音频，不超出其原始长度
    audio_clip = audio_clip.subclipped(0, min(video_clip.duration, audio_clip.duration))

    # 设置音频到视频
    video_with_audio = video_clip.with_audio(audio_clip)

    # 添加字幕
    final_clip = add_text_dynamic(video_with_audio, text)

    print("✅ 视频处理完成")
    return final_clip


def image_merge_video(image_path, audio_path, text):
    """
    图片和音频合成视频（使用MoviePy）
    """
    print("使用MoviePy进行图片视频合成...")

    # 加载音频和图片
    audio_clip = AudioFileClip(audio_path)
    image_clip = ImageClip(image_path, duration=audio_clip.duration)

    # 创建视频并设置尺寸
    video_clip = CompositeVideoClip([image_clip]).resized((1920, 1080))
    video_with_audio = video_clip.with_audio(audio_clip)

    # 添加字幕
    final_clip = add_text_dynamic(video_with_audio, text)

    print("✅ 图片视频合成完成")
    return final_clip


if __name__ == '__main__':
    # handle_frame("./output/downloaded_video1.mp4", "./output/new_downloaded_video2.mp4")
    #
    # # 加载视频文件
    # video1 = VideoFileClip("./output/downloaded_video1.mp4").resized((1080, 1700))
    # video2 = VideoFileClip("./output/downloaded_video2.mp4").resized((1080, 1700))
    #
    # # video1 = VideoFileClip("output_video.mp4")
    # # video2 = VideoFileClip("E:/postgraduate/net/Yolov5-Flask-VUE-master/train/output_video.mp4")
    #
    # # 拼接视频
    # final_clip = concatenate_videoclips([video1, video2])
    #
    # final_clip.write_videofile("./output/new_video.mp4", codec="libx264")


    # generate_audio("./output/downloaded_audio_1.mp3", text, "woman")
    # add_text("./output/new_downloaded_video1.mp4", text, "./output/new_video1.mp4")
    # adjust_audio_speed("./output/downloaded_audio_1.mp3",
    #                    "./output/new_video1.mp4", "./output/downloaded_audio_11.mp3")
    add_audio("./output/new_video1.mp4",
              "./output/downloaded_audio_11.mp3", "./output/new_video11.mp4")

