import io
from pathlib import Path
import tempfile
import base64
from typing import List, Optional, Union

import qrcode
from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont

from .font import FontManager


class QRCodeGenerator:
    """二维码生成器，支持在二维码周围添加文字信息
    QR Code generator with support for adding text information around the QR code
    """

    def __init__(
        self,
        font_manager: FontManager = None,
        background_size: tuple = (350, 180),
        background_color="white",
        qr_size: tuple = (100, 100),
        qr_position: tuple = (20, 40),
        default_font_size: int = 12,
        default_font_color: str = "black",
        output_type: str = "path",
        output_path: Optional[Union[str, Path]] = None,
        border: Optional[Union[dict, bool]] = None,
    ):
        """初始化二维码生成器
        Initialize QR code generator

        Args:
            font_manager: 字体管理器实例 / Font manager instance
            background_size: 背景图尺寸，默认 (350, 180)，不支持vw/vh单位 / Background size, default (350, 180), does not support vw/vh units
            qr_size: 二维码尺寸，默认 (100, 100)，支持rem/vw/vh单位 / QR code size, default (100, 100), supports rem/vw/vh units
            qr_position: 二维码位置，默认 (20, 40)，支持rem/vw/vh单位 / QR code position, default (20, 40), supports rem/vw/vh units
            default_font_size: 默认字体大小，作为rem单位的基准，不支持rem单位 / Default font size, used as the base for rem units, does not support rem units
            default_font_color: 默认字体颜色 / Default font color
            output_type: 输出类型 / Output type default "path", temp, bytes, path, base64
            output_path: 输出文件路径 / Output file path
            border: 边框设置，格式为 {
                "top": 上边距(可选)，支持rem/vw/vh单位，默认20,
                "left": 左边距(可选)，支持rem/vw/vh单位，默认20,
                "right": 右边距(可选)，支持rem/vw/vh单位，默认20,
                "bottom": 下边距(可选)，支持rem/vw/vh单位，默认20,
                "color": 边框颜色(可选)，默认"black",
                "size": 边框粗细(可选)，支持rem/vw/vh单位，默认1
            }
        """
        self.font_manager = font_manager or FontManager()
        
        # 确保default_font_size不是rem单位
        if isinstance(default_font_size, str) and default_font_size.endswith("rem"):
            raise ValueError("default_font_size不能使用rem单位 (default_font_size cannot use rem units)")
        self.default_font_size = default_font_size
        self.default_font_color = default_font_color
        
        # 确保background_size不使用vw/vh单位
        if any(isinstance(v, str) and (v.endswith("vw") or v.endswith("vh")) for v in background_size):
            raise ValueError("background_size不能使用vw或vh单位 (background_size cannot use vw or vh units)")
        
        # 先设置background_size，因为vw/vh单位需要用到它
        self.background_size = self._parse_size_value(background_size)
        self.background_color = background_color
        
        # 处理可能包含rem/vw/vh单位的尺寸和位置
        self.qr_size = self._parse_size_value(qr_size)
        self.qr_position = self._parse_size_value(qr_position)
        
        # 设置边框参数
        self.border = self._parse_border(border)
        
        self.output_type = output_type
        self.output_path = Path(output_path) if output_path else None
        self._temp_file = None
        self._register_font()

    def __enter__(self):
        """上下文管理器入口
        Context manager entry
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出，清理临时文件
        Context manager exit, clean up temporary file
        """
        self.cleanup()

    def cleanup(self):
        """清理临时文件
        Clean up temporary file
        """
        if self._temp_file:
            temp_path = Path(self._temp_file)
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception as e:
                    print(
                        f"警告：清理临时文件失败 (Warning: Failed to clean temporary file) {self._temp_file}: {str(e)}"
                    )
            self._temp_file = None

    def _register_font(self):
        """注册字体
        Register font
        """
        self.font_path = self.font_manager.font_path

    def _parse_size_value(self, value):
        """解析尺寸值，支持rem/vw/vh单位
        Parse size value, supporting rem/vw/vh units
        
        Args:
            value: 可以是数字、字符串或包含这些类型的元组
                   Can be a number, string, or tuple containing these types
        
        Returns:
            解析后的数值或数值元组 / Parsed numeric value or tuple of numeric values
        """
        if isinstance(value, tuple):
            return tuple(self._parse_single_value(v) for v in value)
        else:
            return self._parse_single_value(value)

    def _parse_single_value(self, value):
        """解析单个尺寸值，支持rem/vw/vh单位
        Parse a single size value, supporting rem/vw/vh units
        
        Args:
            value: 数字或字符串，支持以下格式:
                   - 数字: 直接返回
                   - "Xrem": X乘以default_font_size
                   - "Xvw": X%的背景宽度
                   - "Xvh": X%的背景高度
                   Number or string, supports the following formats:
                   - Number: returned directly
                   - "Xrem": X multiplied by default_font_size
                   - "Xvw": X% of background width
                   - "Xvh": X% of background height
        
        Returns:
            解析后的数值 / Parsed numeric value
        """
        if isinstance(value, (int, float)):
            return value
        elif isinstance(value, str):
            if value.endswith("rem"):
                try:
                    rem_value = float(value.rstrip("rem"))
                    return int(rem_value * self.default_font_size)
                except ValueError:
                    raise ValueError(f"无效的rem值 (Invalid rem value): {value}")
            elif value.endswith("vw"):
                try:
                    vw_value = float(value.rstrip("vw"))
                    return int(vw_value * self.background_size[0] / 100)
                except ValueError:
                    raise ValueError(f"无效的vw值 (Invalid vw value): {value}")
            elif value.endswith("vh"):
                try:
                    vh_value = float(value.rstrip("vh"))
                    return int(vh_value * self.background_size[1] / 100)
                except ValueError:
                    raise ValueError(f"无效的vh值 (Invalid vh value): {value}")
            else:
                try:
                    return int(value)
                except (ValueError, TypeError):
                    raise ValueError(f"无效的尺寸值 (Invalid size value): {value}")
        else:
            try:
                return int(value)
            except (ValueError, TypeError):
                raise ValueError(f"无效的尺寸值 (Invalid size value): {value}")

    def _parse_border(self, border: Optional[Union[dict, bool]]) -> dict:
        """解析边框参数"""
        default_border = {
            "top": 20,
            "left": 20,
            "right": 20,
            "bottom": 20,
            "color": "black",
            "size": 1
        }
        
        # 修改这里的逻辑
        if border is None:
            return None  # 返回None表示不绘制边框
        elif border is False:
            return None  # 返回None表示不绘制边框
        elif border is True:
            return default_border
        elif isinstance(border, dict):
            result = default_border.copy()
            # 更新用户提供的边框设置
            for key, value in border.items():
                if key in ["top", "left", "right", "bottom", "size"]:
                    result[key] = self._parse_single_value(value)
                elif key == "color":
                    result[key] = value
            return result
        else:
            return None  # 其他情况也不绘制边框

    def create_info_qrcode(
        self,
        qr_data: str,
        text_info: List[dict],
    ) -> Union[bytes, str]:
        """创建带有文字信息的二维码
        Create QR code with text information

        Args:
            qr_data: 二维码数据内容 / QR code data content
            text_info: 文字信息列表，格式为:
                [
                    {
                        "text": 文本内容,
                        "position": (x, y)，支持rem/vw/vh单位如(10, "2rem")或("50vw", "30vh"),
                        "font_size": 字体大小(可选)，支持rem/vw/vh单位如"1.5rem"或"5vh",
                        "color": 字体颜色(可选),
                        "bold": 是否加粗(可选),
                        "italic": 是否斜体(可选),
                        "text_wrap": 是否自动换行(可选)，默认False,
                        "text_wrap_width": 文字宽度(可选)，支持rem/vw/vh单位，默认"100vw"
                    },
                    {
                        "list": [
                            {
                                "text": 文本内容,
                                "font_size": 字体大小(可选),
                                "color": 字体颜色(可选),
                                "text_wrap": 是否自动换行(可选),
                                "margin": 边距(可选)，格式为(值)或(上下,左右)或(上,右,下,左)
                            },
                            ...
                        ],
                        "margin": 外边距(可选)，默认("0.5rem",),
                        "out_border": 外边框(可选)，格式为(颜色,宽度)或True，默认("black", "0.05rem"),
                        "inner_border": 内边框(可选)，格式为(颜色,宽度)或True，默认("black", "0.05rem"),
                        "column": 列数(可选)，默认1,
                        "width": 宽度(可选)，支持rem/vw/vh单位，默认"100vw",
                        "height": 高度(可选)，支持rem/vw/vh单位，默认"100vh",
                        "start_position": 起始位置(必填)，支持rem/vw/vh单位
                    }
                ]
        """
        # 创建白色背景图 / Create white background
        width, height = self.background_size
        image = PILImage.new("RGB", (width, height), self.background_color)
        draw = ImageDraw.Draw(image)

        # 绘制边框 / Draw border
        if self.border:
            border_left = self.border["left"]
            border_top = self.border["top"]
            border_right = width - self.border["right"]
            border_bottom = height - self.border["bottom"]
            border_size = self.border["size"]
            border_color = self.border["color"]
            
            # 绘制四条边框线 / Draw four border lines
            # 上边框 / Top border
            draw.line([(border_left, border_top), (border_right, border_top)], 
                      fill=border_color, width=border_size)
            # 左边框 / Left border
            draw.line([(border_left, border_top), (border_left, border_bottom)], 
                      fill=border_color, width=border_size)
            # 右边框 / Right border
            draw.line([(border_right, border_top), (border_right, border_bottom)], 
                      fill=border_color, width=border_size)
            # 下边框 / Bottom border
            draw.line([(border_left, border_bottom), (border_right, border_bottom)], 
                      fill=border_color, width=border_size)

        # 生成QR码 / Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=3,
            border=1,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white")

        # 调整QR码大小 / Resize QR code
        qr_image = qr_image.resize(self.qr_size)

        # 将QR码粘贴到背景图上 / Paste QR code to background
        image.paste(qr_image, self.qr_position)

        # 添加文字信息 / Add text information
        for info in text_info:
            try:
                # 处理列表类型 / Process list type
                if "list" in info:
                    self._process_list_info(draw, info)
                # 处理普通文本 / Process normal text
                elif "text" in info and "position" in info:
                    self._process_text_info(draw, info)
                else:
                    print(f"警告：无效的信息格式 (Warning: Invalid info format): {info}")
            except Exception as e:
                print(f"警告：处理信息失败 (Warning: Failed to process info): {str(e)}")
                continue

        # 根据输出类型处理结果 / Handle result based on output type
        if self.output_type == "bytes":
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format="PNG")
            return img_byte_arr.getvalue()
        elif self.output_type == "path":
            if not self.output_path:
                raise ValueError(
                    "输出类型为path时必须提供output_path (output_path is required when output_type is path)"
                )
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(str(self.output_path))
            return str(self.output_path)
        elif self.output_type == "temp":
            self.cleanup()  # 清理旧的临时文件 / Clean up old temporary file
            # 保存到新的临时文件 / Save to new temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                image.save(tmp.name)
                self._temp_file = tmp.name
                return tmp.name
        elif self.output_type == "base64":
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format="PNG")
            return base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")
        else:
            raise ValueError("无效的输出类型 (Invalid output type)")

    def _process_text_info(self, draw, info):
        """处理普通文本信息
        Process normal text information
        """
        text = info["text"]
        coordinates = self._parse_size_value(info["position"])
        
        # 处理font_size中可能的rem/vw/vh单位
        font_size_value = info.get("font_size", self.default_font_size)
        if isinstance(font_size_value, str) and (
            font_size_value.endswith("rem") or 
            font_size_value.endswith("vw") or 
            font_size_value.endswith("vh")
        ):
            font_size = self._parse_single_value(font_size_value)
        else:
            font_size = font_size_value if font_size_value is not None else self.default_font_size
        
        color = info.get("color", self.default_font_color)
        text_wrap = info.get("text_wrap", False)
        
        font = ImageFont.truetype(self.font_path, font_size)
        
        if text_wrap:
            # 处理文本换行
            text_wrap_width_value = info.get("text_wrap_width", "100vw")
            text_wrap_width = self._parse_single_value(text_wrap_width_value)
            
            # 分割文本并绘制
            lines = self._wrap_text(text, font, text_wrap_width)
            y = coordinates[1]
            for line in lines:
                draw.text((coordinates[0], y), line, font=font, fill=color)
                # 根据字体高度计算下一行的y坐标
                y += font.getbbox(line)[3] + 2  # 添加一点行间距
        else:
            # 直接绘制文本
            draw.text(coordinates, text, font=font, fill=color)

    def _process_list_info(self, draw, info):
        """处理列表信息
        Process list information
        """
        list_items = info["list"]
        start_position = self._parse_size_value(info.get("start_position", (2, 2)))
        margin_value = info.get("margin", ("0.5rem",))
        margin = self._parse_margin(margin_value)
        
        # 解析列表宽度和高度
        width_value = info.get("width", "100vw")
        width = self._parse_single_value(width_value)
        height_value = info.get("height", "100vh")
        height = self._parse_single_value(height_value)
        
        # 解析列数
        column_count = info.get("column", 1)
        
        # 解析边框设置，默认为False表示不显示边框
        out_border = info.get("out_border", False)
        inner_border = info.get("inner_border", False)
        
        # 计算每列宽度
        column_width = (width - margin[1] - margin[3]) / column_count
        
        # 存储每行的底部位置和顶部位置，用于绘制行间分隔线和垂直居中
        row_bottom_positions = []
        row_top_positions = []
        
        # 首先计算每个项目的高度，以便后续垂直居中
        item_heights = []
        for item in list_items:
            font_size_value = item.get("font_size", self.default_font_size)
            font_size = self._parse_single_value(font_size_value)
            font = ImageFont.truetype(self.font_path, font_size)
            text = item["text"]
            text_wrap = item.get("text_wrap", False)
            
            if text_wrap:
                # 计算可用宽度
                item_margin = self._parse_margin(item.get("margin", margin_value))
                available_width = column_width - item_margin[1] - item_margin[3]
                
                # 分割文本并计算高度
                lines = self._wrap_text(text, font, available_width)
                total_height = 0
                for line in lines:
                    line_height = font.getbbox(line)[3] + 2  # 添加一点行间距
                    total_height += line_height
                item_heights.append(total_height)
            else:
                # 单行文本高度
                item_heights.append(font.getbbox(text)[3])
        
        # 处理列表项
        for i, item in enumerate(list_items):
            # 计算当前项的行和列
            row = i // column_count
            col = i % column_count
            
            # 获取项目字体大小
            font_size_value = item.get("font_size", self.default_font_size)
            font_size = self._parse_single_value(font_size_value)
            
            # 计算行高和垂直位置
            row_height = 0
            for j in range(row * column_count, min((row + 1) * column_count, len(list_items))):
                row_height = max(row_height, item_heights[j])
            
            # 计算项目位置
            if row == 0:
                item_y = start_position[1] + margin[0]
            else:
                # 使用前一行的底部位置作为当前行的顶部位置
                item_y = row_bottom_positions[row-1] + margin[0]
            
            item_x = start_position[0] + margin[3] + col * column_width
            
            # 记录行的顶部位置
            if row >= len(row_top_positions):
                row_top_positions.append(item_y)
            
            # 获取项目内边距
            item_margin = self._parse_margin(item.get("margin", margin_value))
            
            # 处理项目文本
            text = item["text"]
            color = item.get("color", self.default_font_color)
            text_wrap = item.get("text_wrap", False)
            text_align = item.get("text_align", "start")  # 默认左对齐

            font = ImageFont.truetype(self.font_path, font_size)

            # 计算文本位置，考虑对齐方式
            text_x = item_x + item_margin[3]
            available_width = column_width - item_margin[1] - item_margin[3]

            if text_wrap:
                # 处理换行文本的对齐
                lines = self._wrap_text(text, font, available_width)
                # 垂直居中计算
                item_height = item_heights[i]
                cell_height = row_height + item_margin[0] + item_margin[2]
                text_y = item_y + item_margin[0] + (cell_height - item_margin[0] - item_margin[2] - item_height) / 2
                
                for line in lines:
                    # 根据对齐方式计算x坐标
                    if text_align == "center":
                        line_width = font.getbbox(line)[2]
                        line_x = text_x + (available_width - line_width) / 2
                    elif text_align == "end":
                        line_width = font.getbbox(line)[2]
                        line_x = text_x + available_width - line_width
                    else:  # "start"或其他值
                        line_x = text_x
                    
                    draw.text((line_x, text_y), line, font=font, fill=color)
                    text_y += font.getbbox(line)[3] + 2  # 添加行间距
            else:
                # 处理单行文本的对齐
                text_width = font.getbbox(text)[2]
                
                if text_align == "center":
                    text_x = text_x + (available_width - text_width) / 2
                elif text_align == "end":
                    text_x = text_x + available_width - text_width
                # 对于"start"或其他值，保持原始text_x
                
                # 垂直居中计算
                item_height = item_heights[i]
                cell_height = row_height + item_margin[0] + item_margin[2]
                text_y = item_y + item_margin[0] + (cell_height - item_margin[0] - item_margin[2] - item_height) / 2
                
                draw.text((text_x, text_y), text, font=font, fill=color)
            
            # 记录当前行的底部位置
            row_bottom = item_y + row_height + item_margin[0] + item_margin[2]
            if row >= len(row_bottom_positions):
                row_bottom_positions.append(row_bottom)
            else:
                row_bottom_positions[row] = max(row_bottom_positions[row], row_bottom)
        
        # 绘制内部边框
        if inner_border:
            inner_border_color, inner_border_width_value = inner_border if isinstance(inner_border, tuple) else ("black", "0.05rem")
            inner_border_width = self._parse_single_value(inner_border_width_value)
            
            # 绘制垂直分隔线（列间）
            for col in range(1, column_count):
                x = start_position[0] + margin[3] + col * column_width
                draw.line(
                    [(x, start_position[1]), (x, start_position[1] + height)],
                    fill=inner_border_color,
                    width=inner_border_width
                )
            
            # 绘制水平分隔线（行间）
            for i in range(len(row_bottom_positions) - 1):
                # 在行之间的中间位置绘制分隔线
                line_y = row_bottom_positions[i] + (row_top_positions[i+1] - row_bottom_positions[i]) / 2
                draw.line(
                    [(start_position[0], line_y), (start_position[0] + width, line_y)],
                    fill=inner_border_color,
                    width=inner_border_width
                )
        
        # 绘制外边框
        if out_border:
            out_border_color, out_border_width_value = out_border if isinstance(out_border, tuple) else ("black", "0.05rem")
            out_border_width = self._parse_single_value(out_border_width_value)
            
            # 计算实际内容高度
            actual_height = height
            if row_bottom_positions:
                # 如果有内容，使用最后一行的底部位置作为实际高度
                actual_height = row_bottom_positions[-1] - start_position[1] + margin[2]
            
            # 绘制矩形边框
            draw.rectangle(
                [
                    start_position,
                    (start_position[0] + width, start_position[1] + actual_height)
                ],
                outline=out_border_color,
                width=out_border_width
            )

    def _parse_margin(self, margin_value):
        """解析边距值
        Parse margin value
        
        Args:
            margin_value: 边距值，可以是单个值、两个值或四个值的元组
        
        Returns:
            四个值的元组 (top, right, bottom, left)
        """
        if not isinstance(margin_value, tuple):
            margin_value = (margin_value,)
        
        # 解析每个值
        parsed_values = [self._parse_single_value(v) for v in margin_value]
        
        # 根据值的数量返回完整的边距
        if len(parsed_values) == 1:
            return (parsed_values[0], parsed_values[0], parsed_values[0], parsed_values[0])
        elif len(parsed_values) == 2:
            return (parsed_values[0], parsed_values[1], parsed_values[0], parsed_values[1])
        elif len(parsed_values) == 4:
            return tuple(parsed_values)
        else:
            raise ValueError(f"无效的边距值 (Invalid margin value): {margin_value}")

    def _wrap_text(self, text, font, max_width):
        """将文本按最大宽度换行
        Wrap text by maximum width
        
        Args:
            text: 要换行的文本
            font: 字体对象
            max_width: 最大宽度
        
        Returns:
            换行后的文本行列表
        """
        lines = []
        # 如果文本包含换行符，先按换行符分割
        paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            if not paragraph:
                lines.append('')
                continue
            
            # 中文文本处理：按字符分割而不是按空格
            if any('\u4e00' <= char <= '\u9fff' for char in paragraph):
                current_line = ""
                for char in paragraph:
                    test_line = current_line + char
                    bbox = font.getbbox(test_line)
                    if bbox[2] - bbox[0] <= max_width:
                        current_line = test_line
                    else:
                        lines.append(current_line)
                        current_line = char
                if current_line:
                    lines.append(current_line)
            else:
                # 英文文本处理：按空格分割单词
                words = paragraph.split(' ')
                current_line = words[0]
                
                for word in words[1:]:
                    # 检查添加新单词后是否超过最大宽度
                    test_line = current_line + ' ' + word
                    bbox = font.getbbox(test_line)
                    if bbox[2] - bbox[0] <= max_width:
                        current_line = test_line
                    else:
                        lines.append(current_line)
                        current_line = word
                
                lines.append(current_line)
        
        return lines
