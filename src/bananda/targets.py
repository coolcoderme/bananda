"""Build targets: Android APK, Linux desktop, Windows desktop."""

from __future__ import annotations

from enum import Enum


class Target(str, Enum):
    ANDROID = "android"
    LINUX = "linux"
    WINDOWS = "windows"

    @property
    def language(self) -> str:
        return {
            Target.ANDROID: "kotlin",
            Target.LINUX: "cpp",
            Target.WINDOWS: "csharp",
        }[self]

    @property
    def is_desktop(self) -> bool:
        return self in {Target.LINUX, Target.WINDOWS}

    @property
    def is_android(self) -> bool:
        return self is Target.ANDROID

    @classmethod
    def parse(cls, value: str | Target | None) -> Target:
        if value is None:
            return cls.ANDROID
        if isinstance(value, cls):
            return value
        try:
            return cls(str(value).strip().lower())
        except ValueError as exc:
            raise ValueError(
                f"unknown BanANDa target {value!r}; expected android, linux, or windows"
            ) from exc
