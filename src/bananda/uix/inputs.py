"""Input widgets."""

from __future__ import annotations

from typing import Any

from bananda.uix.widget import Widget


class TextInput(Widget):
    widget_type = "TextInput"

    def __init__(
        self,
        text: str = "",
        hint_text: str = "",
        multiline: bool = False,
        font_size: float = 16,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.text = text
        self.hint_text = hint_text
        self.multiline = multiline
        self.font_size = float(font_size)


class CheckBox(Widget):
    widget_type = "CheckBox"

    def __init__(self, active: bool = False, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.active = bool(active)


class Switch(Widget):
    widget_type = "Switch"

    def __init__(self, active: bool = False, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.active = bool(active)


class Slider(Widget):
    widget_type = "Slider"

    def __init__(
        self,
        min: float = 0,
        max: float = 100,
        value: float = 0,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.min = float(min)
        self.max = float(max)
        self.value = float(value)
