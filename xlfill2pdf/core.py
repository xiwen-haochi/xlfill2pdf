import os
import io
from pathlib import Path
import tempfile
from urllib.request import urlopen

import qrcode
import openpyxl
from PIL import Image as PILImage
from reportlab.platypus import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


class FontManager:
    def __init__(self):
        self._default_font_path = str(Path(__file__).parent / "fonts" / "default.ttf")
        self._custom_font_path = None
        self._font_name = "CustomFont"  # 默认字体名称

    def set_font(self, font_path: str = None, font_name: str = None):
        """设置并注册自定义字体
        Args:
            font_path: 字体文件路径
            font_name: 字体注册名称，默认为 "CustomFont"
        """
        if font_path and Path(font_path).exists():
            self._custom_font_path = font_path
            if font_name:
                self._font_name = font_name

    @property
    def font_path(self):
        """获取当前使用的字体路径"""
        return self._custom_font_path or self._default_font_path

    @property
    def font_name(self):
        """获取当前字体注册名称"""
        return self._font_name


class ExcelProcessor:
    def __init__(
        self,
        font_manager: FontManager,
        prefix: str = "{{",
        suffix: str = "}}",
        qrcode_suffix: str = ".二维码",
        use_default_handlers: bool = True,
        watermark_text: str = None,  # 水印文字
        watermark_alpha: float = 0.1,  # 水印透明度
        watermark_angle: float = -45,  # 水印角度
        watermark_color: tuple = (0, 0, 0),  # 水印颜色 (R,G,B)
    ):
        """替换Excel中的占位符
        Args:
            prefix: 占位符前缀，默认为"{{"
            suffix: 占位符后缀，默认为"}}"
            qrcode_suffix: 二维码后缀，默认为".二维码"
            use_default_handlers: 是否使用默认处理器，默认为True
            watermark_text: 水印文字，默认为None
            watermark_alpha: 水印透明度，默认0.1
            watermark_angle: 水印角度，默认0度（水平）
            watermark_color: 水印颜色，默认黑色(0,0,0)
        """
        self.temp_files = []
        self.font_manager = font_manager
        self.prefix = prefix
        self.suffix = suffix
        self.qrcode_suffix = qrcode_suffix
        self.handlers = {}
        # 水印相关属性
        self.watermark_text = watermark_text
        self.watermark_alpha = watermark_alpha
        self.watermark_angle = watermark_angle
        self.watermark_color = watermark_color

        if use_default_handlers:
            self._register_default_handlers()
        self.__register_font()

    def process_excel_to_pdf(self, excel_path: str, data_dict: dict):
        try:
            temp_excel_path = self.__replace_placeholders(excel_path, data_dict)
            temp_pdf_path = self.__excel_to_pdf(temp_excel_path)
            with open(temp_pdf_path, "rb") as pdf_file:
                pdf_data = pdf_file.read()
            return pdf_data
        finally:
            for temp_file in self.temp_files:
                if temp_file in locals():
                    os.unlink(temp_file)

    def __register_font(self):
        """注册字体到 reportlab"""
        try:
            font_path = self.font_manager.font_path
            pdfmetrics.registerFont(TTFont(self.font_manager.font_name, str(font_path)))
        except Exception as e:
            raise Exception(f"字体注册失败: {e}")

    def _register_default_handlers(self):
        """注册默认的处理器"""
        # 注册二维码处理器
        self.register_handler(f"{self.qrcode_suffix}", self._handle_qrcode)

    def register_handler(self, suffix: str, handler_func):
        """注册自定义处理器
        Args:
            suffix: 处理器对应的后缀，如 ".二维码", ".图片" 等
            handler_func: 处理函数，接收 (cell, field_name, field_value, data_dict) 参数
        """
        self.handlers[suffix] = handler_func

    def _handle_qrcode(self, cell, field_name, field_value, data_dict):
        """处理二维码的默认处理器"""
        qr_cord_img_path = self.generate_qr_code(data_dict.get(field_name))
        img = openpyxl.drawing.image.Image(qr_cord_img_path)
        img.width = 100
        img.height = 100
        cell.value = None
        cell.alignment = openpyxl.styles.Alignment(
            horizontal="center", vertical="center"
        )

        column_letter = openpyxl.utils.get_column_letter(cell.column)
        anchor = f"{column_letter}{cell.row}"

        img.anchor = anchor
        return img, column_letter, cell.row

    def generate_qr_code(self, data):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            img.save(tmp.name)
            self.temp_files.append(tmp.name)
            img_path = tmp.name
        return img_path

    def __replace_placeholders(self, excel_path: str, data_dict: dict):
        if excel_path.startswith("http"):
            try:
                bytes_data = urlopen(excel_path).read()
            except Exception as e:
                raise Exception(f"下载失败: {e}")
            wb = openpyxl.load_workbook(io.BytesIO(bytes_data))
        else:
            wb = openpyxl.load_workbook(excel_path)
        sheet = wb.active

        for row in sheet.iter_rows():
            for cell in row:
                if cell.value and isinstance(cell.value, str):
                    # 检查是否匹配任何已注册的处理器
                    for suffix, handler in self.handlers.items():
                        if cell.value.startswith(self.prefix) and cell.value.endswith(
                            f"{suffix}{self.suffix}"
                        ):
                            field_value = cell.value[
                                len(self.prefix) : -len(f"{suffix}{self.suffix}")
                            ]
                            field_name = field_value.split(".", 1)[0]

                            # 调用对应的处理器
                            result = handler(cell, field_name, field_value, data_dict)
                            if result:
                                img, column_letter, row_num = result
                                sheet.add_image(img)
                                sheet.column_dimensions[column_letter].width = (
                                    img.width / 7
                                )
                                sheet.row_dimensions[row_num].height = img.height * 0.75
                            break
                    else:
                        # 如果没有匹配的处理器，执行普通的占位符替换
                        for key, value in data_dict.items():
                            placeholder = self.prefix + key + self.suffix
                            if placeholder == cell.value:
                                cell.value = cell.value.replace(placeholder, str(value))
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            wb.save(tmp.name)
            self.temp_files.append(tmp.name)
            tmp_path = tmp.name
        return tmp_path

    def _add_watermark(self, canvas_obj, pagesize):
        """添加水印到PDF页面"""
        if not self.watermark_text:
            return

        canvas_obj.saveState()

        # 设置水印文字属性
        canvas_obj.setFont(self.font_manager.font_name, 60)
        r, g, b = self.watermark_color
        canvas_obj.setFillColorRGB(r, g, b, alpha=self.watermark_alpha)

        # 计算水印位置和旋转
        page_width, page_height = pagesize

        # 创建水印网格
        text_width = canvas_obj.stringWidth(
            self.watermark_text, self.font_manager.font_name, 60
        )
        text_height = 60  # 假设高度为字体大小

        # 计算水印间距
        x_spacing = text_width * 2
        y_spacing = text_height * 2

        # 在页面上绘制水印网格
        for y in range(0, int(page_height * 1.5), int(y_spacing)):
            for x in range(0, int(page_width * 1.5), int(x_spacing)):
                canvas_obj.saveState()
                canvas_obj.translate(x, y)
                canvas_obj.rotate(self.watermark_angle)
                canvas_obj.drawString(0, 0, self.watermark_text)
                canvas_obj.restoreState()

        canvas_obj.restoreState()

    def __excel_to_pdf(self, excel_path: str):
        wb = openpyxl.load_workbook(excel_path)
        sheet = wb.active
        tmp_pdf_fd, tmp_pdf_path = tempfile.mkstemp(suffix=".pdf")
        self.temp_files.append(tmp_pdf_path)
        os.close(tmp_pdf_fd)

        margin = 0.3 * inch
        doc = SimpleDocTemplate(
            tmp_pdf_path,
            pagesize=landscape(letter),
            leftMargin=margin,
            rightMargin=margin,
            topMargin=margin,
            bottomMargin=margin,
        )
        data = []
        merged_cells = sheet.merged_cells.ranges
        for row_index, row in enumerate(sheet.iter_rows(), start=1):
            row_data = []
            for col_index, cell in enumerate(row, start=1):
                value = cell.value if cell.value is not None else ""
                for merged_range in merged_cells:
                    if cell.coordinate in merged_range:
                        if cell.coordinate == merged_range.start_cell.coordinate:
                            value = (
                                merged_range.start_cell.value
                                if merged_range.start_cell.value is not None
                                else ""
                            )
                        else:
                            value = ""
                        break

                # 处理图片
                image = None
                for img in sheet._images:
                    if (
                        img.anchor._from.row == row_index - 1
                        and img.anchor._from.col == col_index - 1
                    ):
                        image = img
                        break

                if image:
                    try:
                        img_data = image.ref
                        if hasattr(img_data, "getvalue"):
                            img_bytes = img_data.getvalue()
                        else:
                            img_bytes = img_data

                        pil_img = PILImage.open(io.BytesIO(img_bytes))
                        img_width, img_height = pil_img.size
                        aspect = img_height / float(img_width)

                        max_width = 100
                        img_width = min(img_width, max_width)
                        img_height = img_width * aspect

                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".png"
                        ) as temp_img_file:
                            self.temp_files.append(temp_img_file.name)
                            pil_img.save(temp_img_file.name)
                            value = Image(
                                temp_img_file.name, width=img_width, height=img_height
                            )
                    except Exception as e:
                        value = "图片写入失败"

                row_data.append(value)
            if any(cell != "" for cell in row_data):
                data.append(row_data)

        if not data:
            data = [[""]]
        style = ParagraphStyle(
            "Normal",
            fontName=self.font_manager.font_name,  # 使用字体管理器的字体
            fontSize=8,
            leading=10,
            alignment=1,
        )
        data = [
            [
                Paragraph(str(cell), style) if isinstance(cell, str) else cell
                for cell in row
            ]
            for row in data
        ]

        table = Table(data)
        table_style = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, -1),
                    self.font_manager.font_name,
                ),  # 使用字体管理器的字体
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]
        )
        for merged_range in merged_cells:
            table_style.add(
                "SPAN",
                (merged_range.min_col - 1, merged_range.min_row - 1),
                (merged_range.max_col - 1, merged_range.max_row - 1),
            )
        table.setStyle(table_style)
        elements = [table]

        # 修改 WatermarkCanvas 类的实现
        class WatermarkCanvas(canvas.Canvas):
            def __init__(self, filename, processor=None, **kwargs):
                super().__init__(filename, **kwargs)  # 正确传递所有参数给父类
                self.processor = processor

            def showPage(self):
                if self.processor and self.processor.watermark_text:
                    self.processor._add_watermark(self, landscape(letter))
                super().showPage()

        # 修改 doc.build 调用，传递所有参数
        doc.build(
            elements,
            canvasmaker=lambda filename, **kwargs: WatermarkCanvas(
                filename, processor=self, **kwargs
            ),
        )
        return tmp_pdf_path
