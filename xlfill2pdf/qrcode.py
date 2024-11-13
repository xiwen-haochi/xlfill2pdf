import io
from pathlib import Path
import tempfile
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
    ):
        """初始化二维码生成器
        Initialize QR code generator

        Args:
            font_manager: 字体管理器实例 / Font manager instance
            background_size: 背景图尺寸，默认 (350, 180) / Background size, default (350, 180)
            qr_size: 二维码尺寸，默认 (100, 100) / QR code size, default (100, 100)
            qr_position: 二维码位置，默认 (20, 40) / QR code position, default (20, 40)
            default_font_size: 默认字体大小 / Default font size
            default_font_color: 默认字体颜色 / Default font color
            output_type: 输出类型 / Output type default "path", temp, bytes, path
            output_path: 输出文件路径 / Output file path
        """
        self.font_manager = font_manager or FontManager()
        self.background_size = background_size
        self.background_color = background_color
        self.qr_size = qr_size
        self.qr_position = qr_position
        self.default_font_size = default_font_size
        self.default_font_color = default_font_color
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

    def create_info_qrcode(
        self,
        qr_data: str,
        text_info: dict,
    ) -> Union[bytes, str]:
        """创建带有文字信息的二维码
        Create QR code with text information

        Args:
            qr_data: 二维码数据内容 / QR code data content
            text_info: 文字信息字典，格式为 {
                位置: {
                    "text": 文本内容,
                    "position": (x, y),
                    "font_size": 字体大小(可选),
                    "color": 字体颜色(可选)
                }
            }
        """
        # 创建白色背景图 / Create white background
        width, height = self.background_size
        image = PILImage.new("RGB", (width, height), self.background_color)
        draw = ImageDraw.Draw(image)

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
        for position, info in text_info.items():
            try:
                # 验证必要的键是否存在 / Verify required keys exist
                if "text" not in info or "position" not in info:
                    raise ValueError(
                        f"Missing required keys 'text' or 'position' in {position}"
                    )

                text = info["text"]
                coordinates = info["position"]
                font_size = info.get("font_size", self.default_font_size)
                color = info.get("color", self.default_font_color)

                font = ImageFont.truetype(self.font_path, font_size)
                draw.text(coordinates, text, font=font, fill=color)
            except Exception as e:
                print(
                    f"警告：添加文字失败 (Warning: Failed to add text) {position}: {str(e)}"
                )
                # 跳过处理有问题的文本 / Skip problematic text
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
        else:
            raise ValueError("无效的输出类型 (Invalid output type)")
