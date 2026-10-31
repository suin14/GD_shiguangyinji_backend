from moviepy import ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips
import os

# 图片和文字的列表，图片路径和对应的文字
# images_with_text = [
#     {"image": "path/to/image1.jpg", "text": "这是第一张图片的文字"},
#     {"image": "path/to/image2.jpg", "text": "这是第二张图片的文字"},
#     # 添加更多图片和文字...
# ]

folder_path = "E:/postgraduate/project/zhipu/image"


def read_img(folder_path):
    img_paths = []
    t_img_paths = []
    n = 100000
    count = 0

    for i in range(1, n):
        local_path = os.path.join(folder_path, f'order{i}.png')
        if os.path.exists(local_path):
            t_img_paths.append(local_path)
            img_path = f"file://{local_path}"
            img_paths.append(img_path)
            count += 1
        else:
            print("已经读取完所有的图片！")
            break

    return t_img_paths, img_paths, count


response_list = ["独库公路旁的巨石上，红色的“独库”二字格外醒目。远处的雪山在蓝天白云"
                 "的映衬下显得格外壮丽，山峰的轮廓清晰可见，仿佛在诉说着这片土地的悠久历史和壮美风光。"
                 "站在这里，感受到的不仅是自然的震撼，还有对这片土地的深深敬畏。",
                 "蜿蜒的山路在山谷中盘旋，仿佛一条巨龙在山间穿梭。蓝天如洗，白云悠闲地漂浮在空中，"
                 "与远处的雪山相映成趣。山峰在阳光的照耀下显得更加雄伟壮丽，给人一种无尽的探索欲望。"
                 "站在这条曲折的山路上，心中充满了对未知旅程的期待和对自然美景的赞叹。",
                 "从高空俯瞰，这条蜿蜒曲折的山路如同一条银色的丝带，穿梭在连绵起伏的山峦之间。"
                 "山丘上的植被在阳光下呈现出深浅不一的绿色，与裸露的山体形成鲜明对比。远处的河流如同一条白色的绸带，"
                 "蜿蜒流淌，为这片荒凉的山地增添了几分生机。站在这里，仿佛能感受到大自然的鬼斧神工，"
                 "心中充满了对这片土地的敬畏和对未知旅程的向往。",
                 "这片山谷仿佛是大自然的杰作，两旁的山脉高耸入云，仿佛守护着这片宁静的土地。山谷中的河流蜿蜒流淌，"
                 "清澈的河水在阳光下闪烁着光芒，周围点缀着郁郁葱葱的树木，给这片荒凉的山地增添了几分生机。"
                 "站在这里，感受到的不仅是自然的宁静与美丽，还有对这片土地的深深敬畏。蓝天白云下，这片山谷显得格外宁静与祥和，"
                 "仿佛时间在这里都变得缓慢起来。",
                 "广袤的草原延伸到天际，远处的雪山在阳光下闪耀着银光。雪山的轮廓在蓝天的映衬下显得格外清晰，"
                 "仿佛触手可及。草原上散布着几群牛羊，悠闲地吃着草，给这片宁静的景色增添了几分生机。站在这里，"
                 "感受到的不仅是大自然的壮丽，还有内心的平静与安宁。蓝天白云下，这片景色仿佛一幅美丽的画卷，让人流连忘返。"]


durations = [4, 8, 2, 7, 3]


def split_text(text, max_length):
    """将文本按指定字符数分割"""
    return '\n'.join([text[i:i+max_length] for i in range(0, len(text), max_length)])


def img2videos(t_img_paths, response_list, durations, output_path):
    # 创建视频的宽度和高度
    width, height = 1024, 1024

    # 创建一个视频剪辑列表
    video_clips = []

    if len(t_img_paths) != len(response_list) or len(t_img_paths) != len(durations):
        print("参数数量不匹配！")
        return

    for i in range(len(t_img_paths)):
        # 加载图片
        ad_size = 0.021875

        img_clip = (ImageClip(t_img_paths[i], duration=durations[i])
                    .resized(new_size=(width, height)))

        wrapped_text = split_text(response_list[i], int(width * ad_size))

        text_clip = (TextClip(font='C:/Windows/Fonts/STXINGKA.TTF',
                              text=wrapped_text,
                              font_size=36,
                              color='white',
                              method='label',
                              size=(width - 200, None),
                              text_align='center',
                              horizontal_align='center',
                              duration=durations[i])
                     .with_position(('center', 'bottom')))

        # 将图片和文字剪辑合并
        video_clips.append(CompositeVideoClip([img_clip, text_clip], size=(width, height)))

    # 将所有的剪辑连接起来
    final_clip = concatenate_videoclips(video_clips)

    # 导出视频
    final_clip.write_videofile(output_path, fps=24)


if __name__ == '__main__':
    img_path, _, _ = read_img(folder_path)
    img2videos(img_path, response_list, durations, "output.mp4")

