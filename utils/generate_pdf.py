from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from PIL import Image as PILImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.conf import settings

font_path = settings.BASE_DIR / 'font' / 'simsun.ttc'
pdfmetrics.registerFont(TTFont('SimSun', font_path))


def create_pdf(title, images, descriptions, output_path):
    # 创建一个PDF文件
    doc = SimpleDocTemplate(output_path, pagesize=landscape(letter), rightMargin=inch, leftMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    elements = []

    # 设置样式
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Head', fontSize=20, leading=24, fontName='SimSun', alignment=1))
    styles.add(ParagraphStyle(name='Description', fontSize=14, leading=18, fontName='SimSun',
                              firstLineIndent=28, leftIndent=50, rightIndent=42))

    # 添加标题
    elements.append(Paragraph(title, styles['Head']))
    elements.append(Spacer(1, 0.5 * inch))

    for image_path, description in zip(images, descriptions):
        # 打开图片并获取尺寸
        with PILImage.open(image_path) as img:
            img_width, img_height = img.size
            aspect_ratio = img_width / img_height

            # 根据页面宽度调整图片大小
            img_width = 7.5 * inch
            # img_height = img_width / aspect_ratio
            img_height = 5 * inch

        # 添加图片
        img_element = Image(image_path, width=img_width, height=img_height)
        img_element.hAlign = 'CENTER'
        elements.append(img_element)

        # 添加图片描述
        elements.append(Spacer(1, 0.3 * inch))
        elements.append(Paragraph(description, styles['Description']))
        elements.append(Spacer(1, 0.3 * inch))

    # 构建PDF文件
    doc.build(elements)


if __name__ == '__main__':
    # 使用示例
    title = "我的旅行照片"
    images = ["bear.png", "old.png"]
    descriptions = [
        "这是我在海边的第一张照片。",
        "这张是在山顶拍摄的，风景非常美丽。"
    ]
    output_path = "my_travel_photos.pdf"

    create_pdf(title, images, descriptions, output_path)
