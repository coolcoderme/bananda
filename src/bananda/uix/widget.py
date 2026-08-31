"""Base widget used by the Python-side BanANDa tree."""

from __future__ import annotations

from typing import Any, Callable

from bananda.properties import EventHandler


class Widget:
    """A node in the BanANDa widget tree.

    The Python objects are a compile-time / desktop model of the Android
    views that the transpiler emits as Kotlin.
    """

    widget_type = "Widget"

    def __init__(self, **kwargs: Any) -> None:
        self.children: list[Widget] = []
        self.parent: Widget | None = None
        self.id: str = kwargs.pop("id", "")
        self.width: Any = kwargs.pop("width", "wrap")
        self.height: Any = kwargs.pop("height", "wrap")
        self.size_hint: tuple[Any, Any] = kwargs.pop("size_hint", (1, 1))
        self.opacity: float = float(kwargs.pop("opacity", 1))
        self.background_color: str | None = kwargs.pop("background_color", None)
        self.padding: float = float(kwargs.pop("padding", 0))
        self._handlers: dict[str, list[EventHandler]] = {}
        for key, value in list(kwargs.items()):
            if key.startswith("on_") and callable(value):
                self.bind(**{key: value})
                kwargs.pop(key)
        for key, value in kwargs.items():
            setattr(self, key, value)

    def add_widget(self, child: Widget) -> Widget:
        child.parent = self
        self.children.append(child)
        return child

    def remove_widget(self, child: Widget) -> None:
        if child in self.children:
            self.children.remove(child)
            child.parent = None

    def clear_widgets(self) -> None:
        for child in list(self.children):
            self.remove_widget(child)

    def bind(self, **events: EventHandler) -> None:
        for name, handler in events.items():
            self._handlers.setdefault(name, []).append(handler)

    def unbind(self, **events: EventHandler) -> None:
        for name, handler in events.items():
            registered = self._handlers.get(name, [])
            self._handlers[name] = [h for h in registered if h is not handler]

    def dispatch(self, event: str, *args: Any) -> None:
        for handler in list(self._handlers.get(event, [])):
            handler(self, *args)

    def walk(self) -> list[Widget]:
        nodes = [self]
        for child in self.children:
            nodes.extend(child.walk())
        return nodes

    def dump(self, indent: int = 0) -> str:
        pad = "  " * indent
        extra = self._dump_fields()
        line = f"{pad}{self.widget_type}{extra}"
        parts = [line]
        for child in self.children:
            parts.append(child.dump(indent + 1))
        return "\n".join(parts)

    def _dump_fields(self) -> str:
        fields: list[str] = []
        for name in ("text", "orientation", "hint_text", "id"):
            value = getattr(self, name, None)
            if value not in (None, ""):
                fields.append(f"{name}={value!r}")
        if fields:
            return "(" + ", ".join(fields) + ")"
        return ""

    def __repr__(self) -> str:
        return f"<{self.widget_type} children={len(self.children)}>"
