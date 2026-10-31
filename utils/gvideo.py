from zhipuai import ZhipuAI
import base64
import logging
import time

# 配置日志
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

client = ZhipuAI(api_key="your_api_key")  # 请填写您自己的APIKey

local_image_path = "./image/test2.png"


def generate_video(img_path, content="写实", duration=5):
    # 将本地图片转换为 Base64 编码
    with open(img_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode()

    # 拼接为符合标准的 Base64 URL
    image_url = f"data:image/jpeg;base64,{base64_image}"

    example_content = "在田间漫步"
    example_prompt = ("使用高清摄影风格，一位穿着简约休闲装的女子在金黄色的麦田中漫步，她的表情放松，"
                      "手中拿着一台相机。镜头从正面拍摄，背景是清晰可见的麦穗和蓝天白云，整个画面色彩鲜明，"
                      "细节丰富，气氛宁静，4K高清")

    response0 = client.chat.completions.create(
        model="glm-4-plus",  # 请填写您要调用的模型名称
        messages=[
            {"role": "user", "content": f"作为一名专业的提示词工程师，请根据用户的描述提供专业的提示词用于图像生成。"
                                        f"你可以参考以下例子。样例描述输入:{example_content}。"
                                        f"样例提示词输出:{example_prompt}。"
                                        f"你的回答只含专业具体的提示词信息，不含其他任何冗余信息，"
                                        f"下面是用户输入的描述:{content}"},
        ],
    )

    # 生成视频
    try:
        response1 = client.videos.generations(
            model="cogvideox",
            prompt=response0.choices[0].message.content,
            image_url=image_url,
            size='1024*1024',
            duration=duration
        )
        # logger.debug("生成视频请求成功: %s", response1)
        video_id = response1.id
        return video_id
    except Exception as e:
        # logger.error("生成视频请求失败: %s", e)
        raise

# print(response1)
#
# response2 = client.videos.retrieve_videos_result(
#     id="142217318453270669208187713038440124",
# )


# 定期检查视频生成状态
def check_video_status(v_id):
    while True:
        try:
            response = client.videos.retrieve_videos_result(id=v_id)
            status = response.task_status
            # logger.debug("视频生成状态: %s", status)
            if status == 'SUCCESS':
                # logger.info("视频生成成功: %s", response)
                return response.video_result[0].url
            elif status in ['FAIL']:
                # logger.error("视频生成失败或取消: %s", response)
                break
            elif status == 'PROCESSING':
                # logger.info("视频生成中，当前状态: %s", status)
                time.sleep(10)  # 每隔10秒检查一次
            else:
                # logger.warning("未知状态: %s", status)
                time.sleep(10)  # 未知状态也等待一段时间再重试
        except Exception as e:
            # logger.error("检查视频状态失败: %s", e)
            time.sleep(10)  # 发生错误后也等待一段时间再重试


if __name__ == '__main__':
    video_id = generate_video(local_image_path, content="感受自然的美好")
    response2_url = check_video_status(video_id)

    print(response2_url)
