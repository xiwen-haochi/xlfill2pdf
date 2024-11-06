import pytest
from pathlib import Path
from xlfill2pdf import ExcelProcessor, FontManager
import openpyxl


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
        img_suffix=".png,.图片,.jpeg",
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


@pytest.fixture
def test_excel_path():
    return str(Path(__file__).parent / "resources" / "test.xlsx")


def test_process_excel_to_pdf(processor, test_excel_path, handle_image):
    test_data = {
        "name": "卡卡西",
        "img": r"D:\1fkl\all_test\for_work\xlfill2pdf\tests\resources\img.png",
        "url": "https://www.baidu.com",
        "age": 99,
        "img2": [
            "http://xxx/big-wo-server/template-file/2024/11/e0dd1981-7157-46ca-a50b-bcb4259ae22c-0.png",
            "http://xxx/big-wo-server/template-file/2024/11/e0dd1981-7157-46ca-a50b-bcb4259ae22c-0.png",
        ],
    }
    # processor.register_handler(".png", handle_image)
    # 处理PDF
    pdf_data = processor.process_excel_to_pdf(test_excel_path, test_data)
    assert isinstance(pdf_data, bytes)
    assert len(pdf_data) > 0
    with open("test.pdf", "wb") as f:
        f.write(pdf_data)
