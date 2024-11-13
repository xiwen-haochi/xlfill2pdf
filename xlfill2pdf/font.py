from pathlib import Path


class FontManager:
    """字体管理器
    Font manager for handling custom and default fonts
    """

    def __init__(self):
        self._default_font_path = str(Path(__file__).parent / "fonts" / "default.ttf")
        self._custom_font_path = None
        self._font_name = "DefaultFont"

    def set_font(self, font_path: str = None, font_name: str = None):
        """设置并注册自定义字体
        Set and register custom font

        Args:
            font_path: 字体文件路径 / Font file path
            font_name: 字体注册名称，默认为 "DefaultFont" / Font registration name, defaults to "DefaultFont"
        """
        if font_path and Path(font_path).exists():
            self._custom_font_path = font_path
            if font_name:
                self._font_name = font_name

    @property
    def font_path(self):
        """获取当前使用的字体路径
        Get the current font path in use
        """
        return self._custom_font_path or self._default_font_path

    @property
    def font_name(self):
        """获取当前字体注册名称"""
        return self._font_name
