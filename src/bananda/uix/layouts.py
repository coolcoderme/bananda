"""Layout widgets."""

from __future__ import annotations

from typing import Any

from bananda.uix.widget import Widget


class BoxLayout(Widget):
    widget_type = "BoxLayout"

    def __init__(self, orientation: str = "vertical", spacing: float = 0, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.orientation = orientation
        self.spacing = float(spacing)


class GridLayout(Widget):
    widget_type = "GridLayout"

    def __init__(self, cols: int = 1, rows: int = 0, spacing: float = 0, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.cols = int(cols)
        self.rows = int(rows)
        self.spacing = float(spacing)


class ScrollView(Widget):
    widget_type = "ScrollView"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
