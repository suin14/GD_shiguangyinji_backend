import time
import os

def save(pictures, path):
    """
    保存图片到指定路径
    :param pictures: 图片列表
    :param path: 保存路径
    :return: None
    """
    for picture in pictures:
        # 生成图片文件名,使用时间戳+原始文件名
        timestamp = int(time.time())
        picture_name = f"{timestamp}_{picture.name}"
        # 拼接图片路径
        picture_name = os.path.join(path, picture_name)
            # 保存图片
        with open(picture_name, 'wb+') as destination:
            for chunk in picture.chunks():
                destination.write(chunk)