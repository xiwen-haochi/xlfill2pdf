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


serializer_data_list = [{
    "id": 15573,
    "flow_id": "20022503010625",
    "asset_config_name": "液位仪",
    "status_name": "已停役",
    "region_chain": "第二水厂三期-综合大楼",
    "status_type_name": "end",
    "warehouse_config_name": "第二水厂分库",
    "business_line_name": "厂站",
    "department_name": "ddd",
    "create_time": "2025-03-21 18:23:01",
    "update_time": "2025-04-24 14:29:59",
    "is_active": True,
    "last_handle_user": "admin",
    "department": "28",
    "business_line": "32",
    "asset_type_code": "20",
    "device_type_code": "02",
    "uuid": "25030106",
    "transmiss_code": "2",
    "is_master": True,
    "region_id": 485,
    "region_one_id": 121,
    "region_two_id": 485,
    "region_three_id": None,
    "region_four_id": None,
    "description": None,
    "state": "ok",
    "remark": "1",
    "abandoned_reason": None,
    "stop_reason": None,
    "maintenance_record_last_time": "2025-03-28 10:04:17",
    "relate_device_remark": {},
    "extra_relate_info": [],
    "create_info": {
        "from": "excel",
        "time": "2025-03-21 18:23:00",
        "user": "caihuanhuan",
    },
    "device_info_img": None,
    "device_info_position": None,
    "status": 214,
    "asset_config": 91,
    "warehouse_config": 35,
    "asset_category_dropdown": [21],
    "relate_device": [],
    "Equipment_type--name": "液位仪",
    "Equipment_type": "21",
    "produce_date": "",
    "install_person": "",
    "equipment_name": "液位仪1",
    "model--name": "FMU30-10200",
    "model": "1685",
    "equipment_number": "ywy-01",
    "position": "",
    "install_date": "",
    "manufacturer--name": "MOBRAY",
    "manufacturer": "1098",
}]


def hhhhh():
    font_manager = FontManager()
    font_manager.set_font(
        font_path=str(Path(__file__).parent / "resources" / "STKAITI.TTF")
    )
    with QRCodeGenerator(
            font_manager=font_manager,
            output_type="base64",
            background_size=(3000, 2000),
            qr_size=("40vh", "40vh"),
            qr_position=("5vh", "30vh"),
            default_font_size=140,
        ) as qr:
        for serializer_data in serializer_data_list:
            text_info = [
                {
                    "text": serializer_data["flow_id"],
                    "position": ("5vh", "72vh"),
                    "font_size": "0.8rem",
                },
                {
                    "list": [
                        {
                            "text": "设备标识牌",
                            "font_size": "1.5rem",
                            "text_align": "end",
                        },
                        {
                            "text": f"设备名称：{serializer_data.get('Equipment_type--name', '暂无')}",
                        },
                        {
                            "text": f"设备型号：{serializer_data.get('model--name', '暂无')}",
                        },
                        {
                            "text": f"安装时间：{serializer_data.get('install_person', '暂无')}",
                        },
                    ],
                    "start_position": ("56vh", "30vh"),
                    "out_border": True,
                    # "inner_border": True,
                    "margin": ("0.1rem", 0),
                    "width": "55vw",
                },
            ]
            base64_data = qr.create_info_qrcode(
                qr_data=str(serializer_data["id"]),
                # qr_data="233333",
                text_info=text_info,
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
