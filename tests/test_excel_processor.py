import pytest
from pathlib import Path
from xlfill2pdf import ExcelProcessor, FontManager, QRCodeGenerator
import openpyxl
from PIL import Image
import io


@pytest.fixture
def font_manager():
    font = FontManager()
    font.set_font(font_path=str(Path(__file__).parent / "resources" / "STKAITI.TTF"))
    return font


@pytest.fixture
def processor(font_manager):
    return ExcelProcessor(
        font_manager=font_manager,
        qrcode_suffix=".二维码",
        watermark_text="测试水印",
        watermark_alpha=0.1,
        watermark_angle=-45,
        image_suffix=".png,.图片,.jpeg",
        use_default_qrcode_handlers=False,
        use_default_info_qrcode_handlers=True,
        info_qrcode_suffix=".二维码",
        qrcode_template={
            "title": {
                "text": "设备标识牌",
                "position": (150, 40),
                "font_size": 32,
                "color": "black",
            },
            "name": {
                "text": "设备名称：灭火器",
                "position": (150, 80),
                "font_size": 12,
                "color": "black",
            },
            "model": {
                "text": "设备型号：MPZ/3",
                "position": (150, 100),
                "font_size": 12,
                "color": (0, 0, 139),
            },
            "date": {
                "text": "安装时间：2018-04-29",
                "position": (150, 120),
                "color": "red",
            },
            "code": {
                "text": "JDY20180928-093",
                "position": (25, 145),
            },
        },
    )


@pytest.fixture
def handle_image():
    def _handle_image(cell, field_name, field_value, data_dict):
        # 处理图片的逻辑
        image_path = str(Path(__file__).parent / "resources" / "ttt.png")
        img = openpyxl.drawing.image.Image(image_path)
        img.width = 200
        img.height = 150
        cell.value = None
        column_letter = openpyxl.utils.get_column_letter(cell.column)
        anchor = f"{column_letter}{cell.row}"
        img.anchor = anchor
        return img, column_letter, cell.row

    return _handle_image


def handle_age(cell, field_name, data_dict):
    # 处理图片的逻辑
    age = data_dict.get(field_name)
    if age > 100:
        return "老年"
    else:
        return "青年"


def handle_qrcode(cell, field_name, data_dict):
    font = FontManager()
    font.set_font(font_path=str(Path(__file__).parent / "resources" / "STKAITI.TTF"))
    qrc = QRCodeGenerator(
        font_manager=font,
        qr_size=(50, 50),
        output_type="temp",
    )
    data = qrc.create_info_qrcode(
        data_dict.get(field_name),
        {
            "title": {
                "text": "设备标识牌",
                "position": (150, 40),
                "font_size": 32,
                "color": "black",
            },
            "name": {
                "text": "设备名称：灭火器",
                "position": (150, 80),
                "font_size": 12,
                "color": "black",
            },
            "model": {
                "text": "设备型号：MPZ/3",
                "position": (150, 100),
                "font_size": 12,
                "color": (0, 0, 139),
            },
            "date": {
                "text": "安装时间：2018-04-29",
                "position": (150, 120),
                "color": "red",
            },
            "code": {
                "text": "JDY20180928-093",
                "position": (25, 145),
            },
        },
    )
    img = openpyxl.drawing.image.Image(data)
    # img.width = 100
    # img.height = 50
    cell.value = None
    cell.alignment = openpyxl.styles.Alignment(horizontal="center", vertical="center")

    column_letter = openpyxl.utils.get_column_letter(cell.column)
    anchor = f"{column_letter}{cell.row}"

    img.anchor = anchor
    return img, column_letter, cell.row


@pytest.fixture
def test_excel_path():
    return str(Path(__file__).parent / "resources" / "test.xlsx")


def test_process_excel_to_pdf(processor, test_excel_path, handle_image):
    test_data = {
        "name": "卡卡西copy卡卡西copy卡卡西copy卡卡西copy卡卡西copy卡卡西copy卡卡西copy\n卡卡西copy卡卡西copy卡卡西copy卡卡西copy卡卡西copy",
        "img": r"D:\1fkl\all_test\for_work\xlfill2pdf\tests\resources\img.png",
        "url": "https://www.baidu.com",
        "age": 99,
        # "img2": [
        #     "http://xxx/big-wo-server/template-file/2024/11/e0dd1981-7157-46ca-a50b-bcb4259ae22c-0.png",
        #     "http://xxx/big-wo-server/template-file/2024/11/e0dd1981-7157-46ca-a50b-bcb4259ae22c-0.png",
        # ],
    }
    # processor.register_handler(".png", handle_image)
    # processor.register_handler(".二维码", handler_func=handle_qrcode)
    # 处理PDF
    pdf_data = processor.process_excel_to_pdf(test_excel_path, test_data)
    assert isinstance(pdf_data, bytes)
    assert len(pdf_data) > 0
    with open("test.pdf", "wb") as f:
        f.write(pdf_data)


@pytest.fixture
def text_info():
    """创建测试用的文字信息
    Create test text information
    """
    return {
        "title": {
            "text": "设备标识牌",
            "position": (150, 40),
            "font_size": 32,
            "color": "black",
        },
        "name": {
            "text": "设备名称：灭火器",
            "position": (150, 80),
            "font_size": 12,
            "color": "black",
        },
        "model": {
            "text": "设备型号：MPZ/3",
            "position": (150, 100),
            "font_size": 12,
            "color": (0, 0, 139),
        },
        "date": {
            "text": "安装时间：2018-04-29",
            "position": (150, 120),
            "color": "red",
        },
        "code": {
            "text": "JDY20180928-093",
            "position": (25, 145),
        },
    }


@pytest.fixture
def qr_data():
    """创建测试用的二维码数据
    Create test QR code data
    """
    return "JDY20180928-093"


def test_create_qrcode_bytes(font_manager, text_info, qr_data):
    """测试生成二进制格式的二维码
    Test generating QR code in bytes format
    """
    with QRCodeGenerator(
        font_manager=font_manager,
        output_type="bytes",
    ) as generator:
        result = generator.create_info_qrcode(qr_data, text_info)

        # 验证返回的是字节数据 / Verify returned data is bytes
        assert isinstance(result, bytes)

        # 验证可以被PIL打开 / Verify can be opened by PIL
        image = Image.open(io.BytesIO(result))
        assert image.format == "PNG"
        with open("bytes_test_qrcode.png", "wb") as f:
            f.write(result)


def test_create_qrcode_file(font_manager, text_info, qr_data):
    """测试生成文件格式的二维码
    Test generating QR code as file
    """
    output_path = "test_qrcode.png"

    with QRCodeGenerator(
        font_manager=font_manager,
        qr_size=(50, 50),
        output_type="path",
        output_path=output_path,
    ) as generator:
        result = generator.create_info_qrcode(qr_data, text_info)

        # 验证返回的是字符串路径 / Verify returned path is string
        assert isinstance(result, str)

        # 验证文件存在 / Verify file exists
        assert Path(result).exists()

        # 验证文件可以被PIL打开 / Verify file can be opened by PIL
        image = Image.open(result)
        assert image.format == "PNG"
