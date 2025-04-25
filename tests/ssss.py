import sys
from pathlib import Path

current_path = Path(__file__).parent.parent
print(current_path)
sys.path.insert(0, str(current_path))

from xlfill2pdf import FontManager, QRCodeGenerator
import base64
import io
from PIL import Image


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
