"""Text and progress widgets."""

from __future__ import annotations

from typing import Any

from bananda.uix.widget import Widget


class Label(Widget):
    widget_type = "Label"

    def __init__(
        self,
        text: str = "",
        font_size: float = 16,
        color: str = "#1A1A1A",
        bold: bool = False,
        halign: str = "left",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.text = text
        self.font_size = float(font_size)
        self.color = color
        self.bold = bold
        self.halign = halign


class ProgressBar(Widget):
    widget_type = "ProgressBar"

    def __init__(self, value: float = 0, max: float = 100, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.value = float(value)
        self.max = float(max)
