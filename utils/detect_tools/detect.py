import base64
import json
import os
import pdb
from collections import defaultdict
from datetime import datetime
from html import escape

import face_recognition
import cv2
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont
from dashscope import MultiModalConversation

from graphviz import Digraph
import math

from issue.models import Issue, Picture
import io

def create_json(image_paths, names, output_path):
    json_list = []
    if names == "":
        for i in range(len(image_paths)):
            tmp = {
                "image_path": image_paths[i]
            }
            json_list.append(tmp)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_list, f, ensure_ascii=False, indent=4)
    else:
        if len(image_paths) != len(names):
            print("Image paths and names should have the same length")
            return
        for i in range(len(image_paths)):
            tmp = {
                "image_path": image_paths[i],
                "name": names[i]
            }
            json_list.append(tmp)

        if os.path.exists(output_path):
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    file_content = json.load(f)
                    if not isinstance(file_content, list):
                        raise ValueError("Existing file content is not a list.")
            except json.JSONDecodeError:
                file_content = []
            except Exception as e:
                print(f"处理现有文件时出错: {e}")
                file_content = []
        else:
            file_content = []

        merged_content = file_content + json_list

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged_content, f, ensure_ascii=False, indent=4)
    print("信息已录入")


# def create_detect_json(num, output_path):
#     detect_list = []
#     for i in range(num):
#         tmp = {
#             "image_path": f"E:/postgraduate/project/own/data/some_images/detect/detect{i+1}.png",
#             "name": f"test{i+1}"
#         }
#         detect_list.append(tmp)
#     with open(output_path, 'w', encoding='utf-8') as f:
#         json.dump(detect_list, f, ensure_ascii=False, indent=4)
#     print("人脸库信息已建成")
#
#
# def create_target_json(num,output_path):
#     target_list = []
#     for i in range(num):
#         tmp = {
#             # "image_path": f"E:/postgraduate/project/own/data/some_images/target/target{i+1}.png"
#             "image_path": f"E:/postgraduate/project/own/data/some_images/output/output_new{i + 1}.png"
#         }
#         target_list.append(tmp)
#     with open(output_path, 'w', encoding='utf-8') as f:
#         json.dump(target_list, f, ensure_ascii=False, indent=4)
#     print("测试集已建成")


def load_known_people(known_people):
    known_encodings = []

    for person in known_people:
        image = face_recognition.load_image_file(person['avatar'])
        encodings = face_recognition.face_encodings(image)

        if encodings:
            if len(encodings) > 1:
                print(f"警告:信息库人物图 {person['avatar']} 中人脸数大于1！")
            known_encodings.append(encodings[0])
        else:
            print(f"警告:未在信息库人物图 {person['avatar']} 中检测到人脸！")

    return known_encodings


def load_known_people_single(known_people):
    image = face_recognition.load_image_file(known_people['avatar'])
    encodings = face_recognition.face_encodings(image)

    if encodings:
        if len(encodings) > 1:
            print(f"警告:信息库人物图 {known_people['avatar']} 中人脸数大于1！")
            return None
        return encodings[0]
    else:
        print(f"警告:未在信息库人物图 {known_people['avatar']} 中检测到人脸！")
        return None


def process_image(image_path, user_characters, threshold=0.5):
    import numpy as np

    # 将存储的列表转换回numpy数组
    known_encodings = []
    for user_character in user_characters:
        face_data = user_character["face_data"]
        if face_data is not None and len(face_data) > 0:
            # 将列表转换为numpy数组
            known_encodings.append(np.array(face_data))
        else:
            print(f"警告：用户 {user_character.get('name', '未知')} 没有有效的人脸数据")

    image = face_recognition.load_image_file(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_image)

    # 加载中文字体（推荐使用微软雅黑）
    try:
        font = ImageFont.truetype("msyh.ttc", 14)
    except:
        font = ImageFont.load_default()
        print("警告：未找到中文字体，使用默认字体")

    # 人脸检测和识别逻辑保持不变...
    face_locations = face_recognition.face_locations(image)
    face_encodings = face_recognition.face_encodings(image, face_locations)
    len_detect = len(face_locations)
    description = ""
    left_orders = []
    names = []
    detect_names = []
    annotation = []  # 新增：用于存储人脸标注信息

    # 首先计算所有人脸与所有已知人脸的距离矩阵
    face_character_distances = []
    valid_characters = []

    # 构建有效的人物列表和对应的编码
    for user_character in user_characters:
        face_data = user_character["face_data"]
        if face_data is not None and len(face_data) > 0:
            valid_characters.append(user_character)

    # 为每个检测到的人脸计算与所有已知人脸的距离
    for face_encoding in face_encodings:
        distances = []
        if len(known_encodings) > 0:
            distances = face_recognition.face_distance(known_encodings, face_encoding)
        face_character_distances.append(distances)

    # 使用匈牙利算法或贪心算法进行1对1匹配
    # 这里使用简化的贪心算法：优先匹配距离最小的组合
    face_matches = {}  # face_id -> character_index 的映射

    # 创建所有可能的匹配组合 (face_id, character_index, distance)
    possible_matches = []
    for face_id, distances in enumerate(face_character_distances):
        if len(distances) > 0:
            for char_idx, distance in enumerate(distances):
                if distance < threshold:  # 只考虑在阈值内的匹配
                    possible_matches.append((face_id, char_idx, distance))

    # 按距离排序，优先处理最相似的匹配
    possible_matches.sort(key=lambda x: x[2])

    # 贪心分配：每个人脸和每个人物最多只能匹配一次
    used_faces = set()
    used_characters = set()

    for face_id, char_idx, distance in possible_matches:
        if face_id not in used_faces and char_idx not in used_characters:
            face_matches[face_id] = char_idx
            used_faces.add(face_id)
            used_characters.add(char_idx)

    for face_id, ((top, right, bottom, left), face_encoding) in enumerate(zip(face_locations, face_encodings), 1):
        # 初始化标注信息
        name = "未知"
        color = (0, 0, 255)
        relationship = ""
        avatar = "new URL('@/assets/example/user.png', import.meta.url).href"
        matched_character = None

        # 检查人脸清晰度
        face_region = image[top:bottom, left:right]
        gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()

        # 清晰度阈值
        if lap_var < 100:
            name = "无法识别"
            color = (255, 0, 0)
        else:
            # 检查是否有匹配的人物（face_id从1开始，但数组索引从0开始）
            array_face_id = face_id - 1
            if array_face_id in face_matches:
                char_idx = face_matches[array_face_id]
                matched_character = valid_characters[char_idx]
                name = matched_character["name"]
                relationship = matched_character.get("relationship", "")
                avatar = matched_character.get("avatar", avatar)
                if matched_character["relationship"] != "自己":
                    detect_names.append(matched_character)
                color = (0, 255, 0)
            else:
                # 没有找到匹配的人物，保持为"未知"
                if len(known_encodings) == 0:
                    print("警告：没有可用的人脸编码数据进行比对")

        # 计算检测框中心点坐标
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2

        # 创建annotation条目
        annotation_item = {
            "id": face_id,
            "x": center_x,
            "y": center_y,
            "name": name if matched_character else "",
            "relationship": relationship,
            "avatar": avatar,
            "box": [left, top, right, bottom]
        }
        annotation.append(annotation_item)

        # 使用PIL绘制中文文本
        text_position = (left + 6, bottom - 20)  # 调整文字位置
        draw.rectangle(
            [(left, top), (right, bottom)],
            outline=color,
            width=2
        )
        draw.text(
            text_position,
            name,
            font=font,
            fill=color
        )

        left_orders.append(left)
        names.append(name)

        # # 标注框位置
        # face_center = ((left + right) // 2, (top + bottom) // 2)
        # box_width = right - left
        # box_height = 30
        #
        # # 调整标注框方位
        # if face_center[1] > pil_image.height // 2:
        #     box_position = (left, top - box_height - 10)
        #     arrow_start = (box_position[0] + box_width // 2, box_position[1] + box_height)
        #     arrow_end = (face_center[0], top)
        # else:
        #     box_position = (left, bottom + 10)
        #     arrow_start = (box_position[0] + box_width // 2, box_position[1])
        #     arrow_end = (face_center[0], bottom)
        #
        # # 矩形标注框
        # box_coords = (
        #     box_position[0],
        #     box_position[1],
        #     box_position[0] + box_width,
        #     box_position[1] + box_height
        # )
        # draw.rounded_rectangle(
        #     box_coords,
        #     radius=10,
        #     outline=color,
        #     width=2
        # )
        #
        # draw_arrow(draw, arrow_start, arrow_end, color)
        #
        # text_x = box_position[0] + 10
        # text_y = box_position[1] + (box_height - 14) // 2  # 垂直居中
        # draw.text(
        #     (text_x, text_y),
        #     name,
        #     font=font,
        #     fill=color
        # )

    result_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    # cv2.imwrite(output_path, result_image)
    # print(f"处理结果已保存至：{output_path}")

    indices = list(range(len(left_orders)))
    sorted_indices = sorted(indices, key=lambda x: left_orders[x])
    for n, i in enumerate(sorted_indices):
        if n * 2 < len_detect:
            description += f"左{n+1}:" + names[i] + ";"
        else:
            description += f"右{len_detect - n}:" + names[i] + ";"
    print(description)
    return description, detect_names, result_image, annotation


def draw_arrow(draw, start, end, color, arrow_size=10):
    # 主线
    draw.line([start, end], fill=color, width=2)

    # 箭头角度
    angle = np.arctan2(end[1] - start[1], end[0] - start[0])

    # 箭头两侧
    for angle_offset in [np.pi / 6, -np.pi / 6]:
        arrow_point = (
            end[0] - arrow_size * np.cos(angle + angle_offset),
            end[1] - arrow_size * np.sin(angle + angle_offset)
        )
        draw.line([end, arrow_point], fill=color, width=2)


def load_face_detect(known_encodings, known_names, json_path):
    with open(json_path, 'r', encoding='utf-8') as file:
        test_photo = json.load(file)

    for i, photo in enumerate(test_photo):
        input_image = photo['avatar']
        output_path = f"E:/postgraduate/project/own/data/some_images/output/output_new{i+1}.png"
        # 注意：这个函数调用需要更新以匹配新的process_image签名
        # 但由于参数结构不匹配，这里可能需要重构
        # process_image(input_image, user_characters)  # 需要user_characters而不是known_encodings, known_names
        print(f"警告：load_face_detect函数需要更新以匹配新的process_image签名")


def describe_image(img_path):
    messages = [{"role": "system",
                 "content": [{"text": "请用户上传的图片中存在人脸标注信息，具体表现为人脸附近的标注框，"
                                      "框中有人名信息，或者'未知''无法识别'的报错信息，"
                                      "你需要按从左到右的顺序输出标注信息，"
                                      "示例格式为'左1:lihua | 左2:未知 | 左3:无法识别'，"
                                      "你的输出应该只包含上述信息，没有其他内容。"}]},
                {'role': 'user',
                 'content': [{'image': img_path}]}]
    response = MultiModalConversation.call(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx"
        # api_key=os.getenv('DASHSCOPE_API_KEY'),
        api_key="sk-6aeae9bca1514876a495dd5c74b5ee90",
        model='qwen2.5-vl-72b-instruct',
        messages=messages)

    return response["output"]["choices"][0]["message"].content[0]["text"]


def describe_images(json_path):
    with open(json_path, 'r', encoding='utf-8') as file:
        test_photo = json.load(file)

    for i, photo in enumerate(test_photo):
        input_image = photo['image_path']
        print(describe_image(input_image))


def get_mime_type_from_image(image_path):
    # 使用Pillow打开图像并获取其格式
    with Image.open(image_path) as img:
        mime_type = Image.MIME[img.format]
    return mime_type


# 以恒
def get_location(image_path, user_description):
    url = "https://api.siliconflow.cn/v1/chat/completions"

    mime_type = 'image/' + get_mime_type_from_image(image_path)
    base64_image = encode_image_to_base64(image_path)
    base64_image = f'data:{mime_type};base64,' + base64_image

    payload = {
        "model": "Qwen/Qwen2-VL-72B-Instruct",
        "stream": False,
        "max_tokens": 512,
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "frequency_penalty": 0.5,
        "n": 1,
        "stop": [],
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "image_url": {
                            "detail": "auto",
                            "url": base64_image
                        },
                        "type": "image_url"
                    },
                    {
                        "text": f"请根据用户提供的图片及描述，执行以下环境信息分析任务："
                                f"分析维度（按优先级排序）："
                                f"▪ 地理位置：结合自然景观和人文特征推断大洲/国家/地区"
                                f"▪ 地标识别：识别具有地理标志性的建筑物、自然景观或文化遗址，或对建筑进行外形描述"
                                f"▪ 生物特征：分析图片中出现的植被类型、动物物种及其地域分布特征"
                                f"▪ 气候线索：通过植被状态、光照条件等推断气候类型"
                                f"信息处理要求："
                                f"a) 当图片包含足够分析要素时输出结果"
                                f"b) 当信息不足时不推断该维度，标注为未知"
                                f"输入说明："
                                f"用户补充描述：{user_description}"
                                f"需交叉验证图片特征与文字描述的关联性"
                                f"示例输出：地理位置:中国重庆；地标识别：人民解放碑(或描述外形为碑式建筑也可)；生物特征：无；气候线索：亚热带季风气候"
                                f"你的输出应该只包含上述信息，不含其他任何内容",
                        "type": "text"
                    }
                ]
            }
        ]
    }
    headers = {
        "Authorization": "Bearer sk-vcdctocvtkrgsxoudmnoesrmdpqfpdtngpiuuqjphyxtvaht",
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers)

    # print(response.json()['choices'][0]['message']['content'])
    return response.json()['choices'][0]['message']['content']


# 伟光
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def generate_text(image_path, individuals, locations, user_description):
    url = "https://api.siliconflow.cn/v1/chat/completions"

    mime_type = 'image/' + get_mime_type_from_image(image_path)
    base64_image = encode_image_to_base64(image_path)
    base64_image = f'data:{mime_type};base64,' + base64_image

    payload = {
        "model": "Qwen/Qwen2-VL-72B-Instruct",
        "stream": False,
        "max_tokens": 512,
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "frequency_penalty": 0.5,
        "n": 1,
        "stop": [],
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "image_url": {
                            "detail": "auto",
                            "url": base64_image
                        },
                        "type": "image_url"
                    },
                    {
                        "text": f"请根据用户上传图片以及以下信息生成一段生动自然的照片解读文本:"
                                f"1、人物从左至右的姓名信息为（其中'未知'表明人物信息不明，'无法识别'表明人物比较模糊）:{individuals}"
                                f"2、图片环境信息为:{locations}"
                                f"3、用户在拍摄照片时对相关事件的叙述:{user_description}"
                                f"要求："
                                f"- 使用口语化表达"
                                f"- 强调人物表情与互动细节, 如果人物姓名信息给出，需要点明人物是谁"
                                f"- 突出旅行地特色或家庭记忆点"
                                f"- 自然融入时间和季节线索"
                                f"- 结尾可添加对拍照者心境的推测"
                                f"- 字数控制在100字",
                        "type": "text"
                    }
                ]
            }
        ]
    }
    headers = {
        "Authorization": "Bearer sk-vcdctocvtkrgsxoudmnoesrmdpqfpdtngpiuuqjphyxtvaht",
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers)

    print(response.json()['choices'][0]['message']['content'])
    return response.json()['choices'][0]['message']['content']


# 汇总
def load_event(protagonist, user_characters, user_description, user_time, event, event_id):
    final_texts = []

    for i, photo in enumerate(event):
        filename = os.path.splitext(os.path.basename(photo['url']))[0]
        individuals, detect_names, image, annotation = process_image(photo['url'], user_characters)
        relations, relationship_graph = generate_relation(protagonist, detect_names, filename)
        locations = get_location(photo['url'], user_description)
        final_text = generate_text(photo['url'], individuals, locations, user_description)

        # current_time = datetime.now()
        # formatted_time = current_time.strftime("%Y-%m-%d %H:%M")
        final_texts.append({
            "id": photo['id'],
            "description": final_text,
            "location": locations,
            "time": user_time,
            "relations": relations,
            "detected_image": image,
            "relationship_image": relationship_graph,
            "belongs_to": event_id,
            "face_data": annotation
        })

    return final_texts


def generate_relation(protagonist, detect_characters, file_name):
    # 创建有向图
    dot = Digraph(comment='Relationship Graph', format='png')
    dot.attr(rankdir='TB', layout='neato', overlap='false', splines='true')

    # 全局节点样式设置
    dot.attr('node',
             shape='none',
             fixedsize='true',
             width='2',  # 统一节点宽度
             height='2',  # 统一节点高度（包含文字）
             imagescale='true',
             labelloc='b',  # 标签位于节点底部
             fontsize='14')

    dot.attr(fontname='SimHei', encoding='utf-8')  # 改为系统中的中文字体
    dot.node_attr.update(fontname='SimHei')  # 设置节点字体
    dot.edge_attr.update(fontname='SimHei')  # 设置边字体

    # 添加主人公节点（中心位置）
    dot.node(
        'protagonist',
        label=f'<<font point-size="16">{protagonist["name"]}</font>>',
        image=protagonist['avatar'],
        pos='0,0!',
        _attributes={'imagepos': 'tc'}  # 图片顶部居中
    )

    # 添加其他角色
    total = len(detect_characters)
    radius = 4  # 分布半径

    relations_list = []

    for i, char in enumerate([c for c in detect_characters]):
        # 计算角度（增加起始角度偏移）
        angle = 360 / total * i - 90  # 从顶部开始分布
        x = radius * math.cos(math.radians(angle))
        y = radius * math.sin(math.radians(angle))

        # 创建带图片和文字的复合节点
        dot.node(
            f'char_{i}',
            label=f'<<font point-size="14">{char["name"]}</font>>',
            image=char['avatar'],
            pos=f'{x},{y}!',
            _attributes={'imagepos': 'tc'}  # 图片顶部居中
        )

        # 创建连线（增加曲线效果）
        dot.edge(
            'protagonist',
            f'char_{i}',
            label=char['relationship'],
            fontsize='12',
            fontcolor='#666666',
            color='#888888',
            penwidth='1.2',
            labelfloat='true',
            labeldistance='2.5'
        )

        relations_list.append({char.get("name", ""): char.get("relationship", "")})

    relations = ",".join(f"{key}:{value}" for d in relations_list for key, value in d.items())
    # 使用 pipe 方法生成 PNG 数据
    png_data = dot.pipe(format='png')

    # 将 PNG 数据转换为文件对象
    file_object = io.BytesIO(png_data)
    file_object.name = f'{file_name}_relationship_graph.png'

    return relations, file_object


if __name__ == "__main__":
    # 需求：传入人物库信息（包括人脸图片、人物名字），以及待测图片，在待测图片上标注出人物信息，并根据人物信息、检测到的地理环境信息生成描述文本
    # 前端网页需求：用户可以上传人物信息、待检测照片，最终可以输出检测后的照片以及文本即可。

    # 创建人物库信息，这里展示用json文件替代，传入图片路径和人物名字列表。如果写入的json文件有内容，会新增在后面。
    # test_image = ["E:/postgraduate/project/own/data/some_images/detect/detect1.png"]
    # test_name = ["王诗琪"]
    # test_path = "./test_detect.json"
    # create_json(test_image, test_name, test_path)
    #
    # # 创建检测库信息，这里展示用json文件替代，传入图片路径列表，人物名置为空字符串。如果写入的json文件有内容，会新增在后面。
    # target_image = ["E:/postgraduate/project/own/data/some_images/target/target1.png"]
    # target_name = ""
    # target_path = "./test_target.json"
    # create_json(target_image, target_name, target_path)
    #
    # # 处理人物库人脸信息，用于后续比对
    # known_encodings, known_names = load_known_people(test_path)
    #
    # # 对检测照片进行人物标注、地理位置检测和文本生成。photo_path存储标注人物后的图片，output_path存储输出的最终文本。
    # output_path = "./test_output.json"
    # photo_path = "./some_images/output"
    # load_test(known_encodings, known_names, target_path, photo_path, output_path)

    detect_path = "../resource/detect_face.json"
    target_path = "../resource/target_face.json"
    photo_path = "../output/images"
    output_path = "../output/test_output.json"
    # known_encodings, known_names = load_known_people(detect_path)
    # load_test(detect_path, known_encodings, known_names, target_path, photo_path, output_path)
