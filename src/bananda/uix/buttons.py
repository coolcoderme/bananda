"""Button widgets."""

from __future__ import annotations

from typing import Any

from bananda.uix.widget import Widget


class Button(Widget):
    widget_type = "Button"

    def __init__(
        self,
        text: str = "",
        font_size: float = 16,
        color: str = "#3D2E00",
        background_color: str = "#F4C430",
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("background_color", background_color)
        super().__init__(**kwargs)
        self.text = text
        self.font_size = float(font_size)
        self.color = color
