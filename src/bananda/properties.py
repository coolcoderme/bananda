"""Kivy-inspired observable properties used by the Python widget tree."""

from __future__ import annotations

from typing import Any, Callable


class Property:
    """Descriptor that stores a value and notifies the owner on change."""

    def __init__(self, default: Any = None):
        self.default = default
        self.name = ""
        self.private = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name
        self.private = f"_{name}"

    def __get__(self, obj: Any, objtype: type | None = None) -> Any:
        if obj is None:
            return self
        return getattr(obj, self.private, self.default)

    def __set__(self, obj: Any, value: Any) -> None:
        old = getattr(obj, self.private, self.default)
        setattr(obj, self.private, value)
        if old != value:
            dispatch = getattr(obj, "dispatch", None)
            if callable(dispatch):
                dispatch(f"on_{self.name}", value)


class StringProperty(Property):
    def __init__(self, default: str = ""):
        super().__init__(default)


class NumericProperty(Property):
    def __init__(self, default: float = 0):
        super().__init__(default)


class BooleanProperty(Property):
    def __init__(self, default: bool = False):
        super().__init__(default)


class ObjectProperty(Property):
    def __init__(self, default: Any = None):
        super().__init__(default)


class ListProperty(Property):
    def __init__(self, default: list | None = None):
        super().__init__(list(default) if default is not None else [])


EventHandler = Callable[..., Any]
