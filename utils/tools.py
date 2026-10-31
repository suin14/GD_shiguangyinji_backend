from video import generate_video, check_video_status
from generate_pdf import create_pdf
from handle import handle_frame, adjust_audio_speed, add_audio, concat_videos
from generate_video import read_img, img2videos
from ali import generate_sentence, get_title, repaint
from ali_character import (generate_audio, generate_image, character_detect,
                           character_generate, get_task_status,
                           download_video, add_text, generate_ref_image)


if __name__ == '__main__':
    # 添加文字进视频，涉及到字体，可能根据实际字体所在文件夹改一下参数，在代码中搜索 C:/Windows/Fonts 可以找到修改的地方

    # 1、根据图片和用户描述生成视频（视频），时长由参数duration决定（5或者10）
    # ps:这里我的资源包过期了，要试用的话需要重新去智谱AI官网用新账号领一下资源包，并在video.py中将"your_api_key"替换成实际值
    image_path = "./image/test1.png"
    description = "感受自然的美好"
    video_output_path = "./test/test1.mp4"
    # 获取任务id
    video_id = generate_video(image_path, description, duration=5)
    # 获取任务状态，直到返回生成视频的url链接
    video_url = check_video_status(video_id)
    # 根据url下载视频到本地
    download_video(video_url, video_output_path)

    # 2、根据传入的序列图片（文件夹下命名为order{i}.jpg，会按照数字顺序依次读取），生成对应的文案信息，拟一个标题，并保存为pdf
    images_folder = "./image"
    images_save_folder = "./test"
    pdf_output_path = "./test/test_pdf.pdf"
    # 将路径存入列表，这里由三个参数，其中前两个都是文件路径的列表，
    # 不过格式稍有不同（第二个用于传给大模型），第三个参数count是读取到的图片数量
    t_img_paths, model_img_paths, count = read_img(images_folder)
    # 为每个图片生成文案信息，保存在列表response_list中，同时合成为一个字符串保存在t_content中
    response_list, t_content = generate_sentence(model_img_paths, count)
    # 根据所有的文案信息生成标题
    title = get_title(t_content)
    # 可选：根据文案信息重绘各图，并保存在指定路径，图像风格参数如下
    # <auto>：默认值，由模型随机输出图像风格。
    # <photography>：摄影。
    # <portrait>：人像写真。
    # <3d cartoon>：3D卡通。
    # <anime>：动画。
    # <oil painting>：油画。
    # <watercolor>：水彩。
    # <sketch>：素描。
    # <chinese painting>：中国画。
    # <flat illustration>：扁平插画。
    # new_img_paths = repaint(response_list, images_save_folder, count, style='watercolor')
    # 根据原始图片或者重绘的图片生成pdf
    create_pdf(title, t_img_paths, response_list, pdf_output_path)
    # create_pdf(title, new_img_paths, response_list, pdf_output_path)

    # 3、根据传入的序列图片（文件夹下命名为order{i}.jpg，会按照数字顺序依次读取），以及对应的文案信息，输出成一个图片组成的视频（没有声音）
    video_output_path = "./test/test_video.mp4"
    durations = [4 for i in range(count)]
    # durations是一个列表，用于规定每个图片展示的时长
    img2videos(t_img_paths, response_list, durations, video_output_path)

    # 4、为视频添加文字和音频信息
    origin_video_path1 = "./output/downloaded_video1.mp4"
    handled_video_path1 = "./test/handled_video1.mp4"
    mid_video_path1 = "./test/mid_video1.mp4"
    new_video_path1 = "./test/new_video1.mp4"
    text1 = "坐在草地上，呼吸着新鲜的空气，我感觉大自然是如此的美好"
    origin_audio_path1 = "./test/downloaded_audio1.mp3"
    audio_path1 = "./test/new_audio1.mp3"
    origin_video_path2 = "./output/downloaded_video2.mp4"
    handled_video_path2 = "./test/handled_video2.mp4"
    mid_video_path2 = "./test/mid_video2.mp4"
    new_video_path2 = "./test/new_video2.mp4"
    text2 = "在高粱田间漫步，感受丰收的喜悦之情"
    origin_audio_path2 = "./test/downloaded_audio2.mp3"
    audio_path2 = "./test/new_audio2.mp3"
    # 第三个参数用于确定声线，只接受man和woman
    generate_audio(origin_audio_path1, text1, "female")
    generate_audio(origin_audio_path2, text2, "female")
    # 模型生成的视频下载下来尾帧似乎有问题，建议先处理一下
    handle_frame(origin_video_path1, handled_video_path1)
    handle_frame(origin_video_path2, handled_video_path2)
    # 将音频信息添加到视频中，这里需要先将音频时长和视频时长匹配，传入参数为原音频，原视频和输出音频保存地址
    # 音频时长最好不要和视频时长差太多，否则调整语速可能会出问题
    adjust_audio_speed(origin_audio_path1, handled_video_path1, audio_path1)
    adjust_audio_speed(origin_audio_path2, handled_video_path2, audio_path2)
    # 将音频添加进视频
    add_audio(handled_video_path1, audio_path1, mid_video_path1)
    add_audio(handled_video_path2, audio_path2, mid_video_path2)
    # 将文本添加进视频
    add_text(mid_video_path1, text1, new_video_path1)
    add_text(mid_video_path2, text2, new_video_path2)
    # 可以考虑最后用os.remove将中间步骤的视频删去

    # 5、将视频拼接到一起
    concat_output_path = "./test/concat_videos.mp4"
    # 将要拼接的视频地址存成列表传入
    video_files = [new_video_path1, new_video_path2]
    concat_videos(video_files, concat_output_path)

    # 6、数字人（用于视频中的用户自白部分）
    introduction = ("您好啊！我是张伟，刚泡了一壶茶，正好闲下来。不知道您愿不愿意和我一起聊聊天，"
                    "分享一下您的故事？我特别喜欢听别人的人生经历，总能从中学到很多。")
    character_audio_path = "./test/character_audio.mp3"
    character_url = "https://gitee.com/lin-lingwww/resource/raw/master/image/new_character.jpg"
    audio_url = "https://gitee.com/lin-lingwww/resource/raw/master/audio/character_audio.mp3"
    character_out_path = "./test/character_out.mp4"
    # 可选：如果用户不想上传照片，可根据描述用模型生成数字人形象，用户可以上传参考照片
    character_save_path = "./test/character.jpg"
    refer_path = "./test/test.webp"
    prompt = "开朗的年轻人"
    # 有/无参考图两种形式
    # 图像风格参数如下
    # <auto>：默认值，由模型随机输出图像风格。
    # <photography>：摄影。
    # <portrait>：人像写真。
    # <3d cartoon>：3D卡通。
    # <anime>：动画。
    # <oil painting>：油画。
    # <watercolor>：水彩。
    # <sketch>：素描。
    # <chinese painting>：中国画。
    # <flat illustration>：扁平插画。
    # generate_image(character_save_path, prompt, "<portrait>")
    generate_ref_image(character_save_path, prompt, "<portrait>", refer_path)
    # 用户自白语录
    generate_audio(character_audio_path, introduction, "man")
    # 用户上传图像检测（是否适合生成数字人）。这里上传图片和音频只能是http链接的形式
    if character_detect(character_url):
        character_task_id = character_generate(character_url, audio_url)
        character_download_url = get_task_status(character_task_id)
        download_video(character_download_url, character_out_path)
    else:
        print("上传图片不适合生成数字人!")
