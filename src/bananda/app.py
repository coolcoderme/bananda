"""Application base class — Kivy-like ``App`` that can run or transpile."""

from __future__ import annotations

import os
from typing import Any

from bananda.uix.widget import Widget


class App:
    """Subclass this and implement :meth:`build` to describe the UI.

    On a desktop Python interpreter, :meth:`run` builds the widget tree and
    optionally opens a Tk preview. That path is for development only.

    Shipping an Android app never embeds this interpreter. ``bananda build``
    converts the subclass to Kotlin and compiles a native APK.
    """

    title: str = "BanANDa"

    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.root: Widget | None = None

    def build(self) -> Widget:
        raise NotImplementedError(f"{type(self).__name__}.build() must return a widget tree")

    def on_start(self) -> None:
        return None

    def on_stop(self) -> None:
        return None

    def on_pause(self) -> None:
        return None

    def on_resume(self) -> None:
        return None

    def run(self) -> Widget:
        self.root = self.build()
        self.on_start()
        headless = os.environ.get("BANANDA_HEADLESS") == "1" or not os.environ.get("DISPLAY")
        if headless:
            print(self.root.dump())
            return self.root
        from bananda.desktop.tk_backend import launch

        launch(self, self.root)
        return self.root
