import pytest
from pathlib import Path
from xlfill2pdf import ExcelProcessor
from xlfill2pdf import FontManager
import openpyxl


@pytest.fixture
def font_manager():
    font = FontManager()
    font.set_font(font_path=str(Path(__file__).parent / "resources" / "STKAITI.TTF"))
    print(f"Current font path: {font.font_path}")
    print(f"Current font name: {font.font_name}")
    return font


@pytest.fixture
def processor(font_manager):
    return ExcelProcessor(
        font_manager=font_manager,
        qrcode_suffix=".二维码",
        watermark_text="机密",
        watermark_alpha=0.7,
        watermark_angle=-45,
        watermark_color=(216, 0, 54),
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
        "name": "Test User",
        "id": "12345",
    }
    processor.register_handler(".png", handle_image)
    # 处理PDF
    pdf_data = processor.process_excel_to_pdf(test_excel_path, test_data)
    assert isinstance(pdf_data, bytes)
    assert len(pdf_data) > 0

    # 保存PDF时使用更明确的路径
    output_path = Path(__file__).parent / "output" / "test.pdf"
    output_path.parent.mkdir(exist_ok=True)  # 确保输出目录存在
    with open(output_path, "wb") as f:
        f.write(pdf_data)
    print(f"PDF saved to: {output_path}")
