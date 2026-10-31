import os
import dashscope
import base64

from .generate_pdf import create_pdf
import pdb
import requests

from http import HTTPStatus
from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath

folder_path = "E:/postgraduate/project/zhipu/image"
save_folder = "./output"


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


def generate_message(im, index):
    n_message = [
        {
            "role": "system",
            "content": [
                {
                    "text": f"你是个专业的博客写手，我会给你几张我在穿越新疆独库公路时拍的图片，"
                            f"请你从我的视角为每一张图写一份中文文案，内容包括对所拍图片的描绘和我的感想，"
                            f"语气要自然，描述景色时直接进入对景色的描绘，不要诸如'这张照片描绘了'一类的开头语。\n\n"
                            f"输出内容不要包含其他任何冗余信息。",
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "image": im
                },
                {
                    "text": f"这是第{index}张图。",
                }
            ]
        }
    ]
    return n_message


def modify_message(im, tc, index):
    n_message = [
        {
            "role": "system",
            "content": [
                {
                    "text": f"你是个专业的博客写手，接受用户拍的图片，"
                            f"请你从用户的视角为每一张图写一份中文文案，内容包括对所拍图片的描绘和用户的感想，"
                            f"语气要自然，描述景色时直接进入对景色的描绘，不要诸如'这张照片描绘了'一类的开头语。\n\n"
                            f"输出内容不要包含其他任何冗余信息。",
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "image": im
                },
                {
                    "text": f"这是第{index}张图。以及前几张图的文案信息：{tc}。可以供你参考，请尽量不要让文案信息重复。"
                }
            ]
        }
    ]
    return n_message


def generate_title(tc):
    n_message = [
        {
            "role": "system",
            "content": f"你是个专业的博客写手，接受用户给自己拍的图片所写的文案信息作为参考，"
                       f"为文案内容起一个标题。\n\n"
                       f"输出内容不要包含其他任何冗余信息。",
        },
        {
            "role": "user",
            "content": f"这是我为我拍的图所写的文案信息：{tc}。"
        }
    ]
    return n_message


def generate_sentence(img_paths, count):
    response_list = []
    t_content = ""

    for i in range(count):
        if i == 0:
            t_message = generate_message(img_paths[i], i + 1)
        else:
            t_message = modify_message(img_paths[i], t_content, i + 1)

        response = dashscope.MultiModalConversation.call(
            # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
            api_key="sk-31fcd5c08ae74de8a713c170bb23b7d3",
            model='qwen-vl-max-2025-04-08',
            messages=t_message
        )
        response_list.append(response["output"]["choices"][0]["message"].content[0]["text"])
        t_content = t_content + f"第{i}张图的文案：" + response_list[i] + "\t"
        print(f"已经完成了第{i + 1}张图片的文案生成！")
    return response_list, t_content


def get_title(t_content):
    title_message = generate_title(t_content)

    response = dashscope.Generation.call(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        api_key="sk-31fcd5c08ae74de8a713c170bb23b7d3",
        model="qwen-plus-2025-04-28",  # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        messages=title_message,
        result_format='message'
    )

    title = response["output"]["choices"][0]["message"].content
    return title


def repaint(response_list, save_folder, count, style):
    new_img_paths = []

    for i in range(count):
        rsp = dashscope.ImageSynthesis.call(
            api_key="sk-31fcd5c08ae74de8a713c170bb23b7d3",
            model=dashscope.ImageSynthesis.Models.wanx_v1,
            prompt=response_list[i],
            n=1,
            style=style,
            size='1024*1024')
        print('response: %s' % rsp)
        if rsp.status_code == HTTPStatus.OK:
            # 在当前目录下保存图片
            for result in rsp.output.results:
                # file_name = PurePosixPath(unquote(urlparse(result.url).path)).parts[-1]
                # with open('./%s' % file_name, 'wb+') as f:
                # f.write(requests.get(result.url).content)
                file_name = f"image_{i + 1}.png"
                full_path = os.path.join(save_folder, file_name)
                with open(full_path, 'wb+') as f:
                    f.write(requests.get(result.url).content)
                print(f'Successfully saved {full_path}')
                new_img_paths.append(full_path)
        else:
            print('sync_call Failed, status_code: %s, code: %s, message: %s' %
                  (rsp.status_code, rsp.code, rsp.message))

    return new_img_paths


if __name__ == '__main__':
    t_img_paths, img_paths, count = read_img(folder_path)

    response_list, t_content = generate_sentence(img_paths, count)

    title = get_title(t_content)

    new_img_paths = repaint(response_list, save_folder, count)

    output_path = "ali_generate_img.pdf"

    # create_pdf(title, t_img_paths, response_list, output_path)

    create_pdf(title, new_img_paths, response_list, output_path)
