import sys
from pathlib import Path

current_path = Path(__file__).parent.parent
print(current_path)
sys.path.insert(0, str(current_path))

from xlfill2pdf import FontManager, QRCodeGenerator
import base64
import io
from PIL import Image


text_info = [
    { # 可以有多个这样的字典，其中position和text必填
        "text": "设备标识牌",
        "position": (150, 40),
        "font_size": 32,
        "color": "black",
        "text_wrap": False, # 是否自动换行,默认是False 
        "text_wrap_width": "100vw", # 文字的宽度，可以使用vw vh rem，也可以是数字，默认是100vw,，如果text_wrap为True,超过text_wrap_width就自动换行
    },
        { # 可以有多个这样的字典，其中position和text必填
        "text": "设备标识牌2",
        "position": (200, 80),
        "font_size": 32,
        "color": "black", 

    },
    {
        "list": # 特殊样式list类似列表可以有多列，list平级的有start_position,是必填的，指定这个list左上方位置，
            #数组内容内部没有position，只能根据margin计算出位置, text_wrap_width也是根据width和margin和column计算出的
            [
            {
                "text": "文本内容",
                "font_size": "5vh",
                "color": "black",
                "text_wrap": True, # 是否自动换行,默认是False
                "margin": (
                    2,
                ),  # 如果len等于1表示周围都要空这么多，也可以使用rem不和vh或者wh，是(2, 4)len是2的话分别标识上下和左右，(2,2,3,4)len是4的话分别标识上右下左
            },
            {
                "text": "文本内容2",
                "position": (2, 2),
                "font_size": "5vh",
                "color": "black",
            },
        ],
        "margin": (
            "0.5rem",
        ), # 外部有margin，默认内部所有数据使用外部的margin，也可以使用rem不和vh或者wh，除非内部也有，则使用内部的，默认是("0.5rem",)
        "out_border": ("black", "0.2rem"),# out_border 表示list有外部边框，两值分别标识颜色和宽度，也可以是True，表示使用默认的边框默认是("black", "0.2rem")
        "inner_border": ("black", "0.2rem"),# inner_border 表示list有内部边框，两值分别标识颜色和宽度，也可以是True，表示使用默认的边框默认是("black", "0.2rem")
        "column": 1, #数组标识有几列，默认是1列
        "width": "100vw", # list的宽度，可以使用vw vh rem，也可以是数字，默认是100vw
        "height": "100vh", # list的高度，可以使用vw vh rem，也可以是数字，默认是100vh
        "start_position": (2, 2), # list的位置，可以使用vw vh rem，也可以是数字，默认是(2, 2)
    },
]


def hhhhh():
    font_manager = FontManager()
    font_manager.set_font(
        font_path=str(Path(__file__).parent / "resources" / "STKAITI.TTF")
    )
    with QRCodeGenerator(
        font_manager=font_manager,
        output_type="base64",
        background_size=("25rem", 2200),
        qr_size=("5rem", "5rem"),
        qr_position=("10vw", "5rem"),
        default_font_size=140,
        default_font_italic=True,
        default_font_bold=True,
        border=True,
    ) as qr:
        base64_data = qr.create_info_qrcode(
            qr_data="22222",
            text_info=[
                {
                    "list": [
                        {"text": "设备名称：测试设备dddddddddddddd和你好好或或或或dddddddddddddddddddd", "font_size": 120, "text_wrap": True},
                        {"text": "设备型号：XYZ-100", "font_size": 120},
                        {"text": "安装时间：2023-05-15", "font_size": 120},
                    ],
                    "start_position": ("30vw", "30vh"),
                    "column": 1,
                    "out_border": True,
                    "inner_border": True,
                    "width": "50vw",
                    # "height": "50vh",
                }
            ],
        )
    out_path = r"D:\1fkl\xlfill2pdf\ttt.png"
    base64_to_image(base64_data, out_path)


def base64_to_image(base64_string, output_path):

    # 将Base64字符串解码为字节数据
    image_bytes = base64.b64decode(base64_string)

    # 使用PIL库将字节数据转换为图像对象
    image = Image.open(io.BytesIO(image_bytes))

    # 保存图像到指定路径
    image.save(output_path)


if __name__ == "__main__":
    hhhhh()
