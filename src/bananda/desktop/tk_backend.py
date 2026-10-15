"""Tiny Tkinter preview so ``App.run()`` works while developing on a desktop."""

from __future__ import annotations

import tkinter as tk
from typing import Any

from bananda.uix.buttons import Button
from bananda.uix.inputs import CheckBox, Slider, Switch, TextInput
from bananda.uix.labels import Label, ProgressBar
from bananda.uix.layouts import BoxLayout, GridLayout, ScrollView
from bananda.uix.widget import Widget


def launch(app: Any, root_widget: Widget) -> None:
    window = tk.Tk()
    window.title(getattr(app, "title", "BanANDa"))
    window.minsize(360, 640)
    window.configure(bg="#FFF8E1")
    _mount(window, root_widget)
    window.mainloop()
    if hasattr(app, "on_stop"):
        app.on_stop()


def _mount(parent: tk.Misc, widget: Widget) -> tk.Misc:
    if isinstance(widget, BoxLayout):
        frame = tk.Frame(parent, bg=_bg(widget, "#FFF8E1"))
        side = tk.TOP if widget.orientation == "vertical" else tk.LEFT
        fill = tk.BOTH
        frame.pack(side=tk.TOP, fill=fill, expand=True, padx=int(widget.padding), pady=int(widget.padding))
        for child in widget.children:
            child_widget = _mount(frame, child)
            child_widget.pack(
                side=side,
                fill=tk.X if widget.orientation == "vertical" else tk.Y,
                expand=True,
                padx=int(widget.spacing),
                pady=int(widget.spacing),
            )
        return frame
    if isinstance(widget, GridLayout):
        frame = tk.Frame(parent, bg=_bg(widget, "#FFF8E1"))
        frame.pack(fill=tk.BOTH, expand=True)
        cols = max(1, widget.cols)
        for index, child in enumerate(widget.children):
            child_widget = _mount(frame, child)
            child_widget.grid(row=index // cols, column=index % cols, padx=4, pady=4, sticky="nsew")
        return frame
    if isinstance(widget, ScrollView):
        canvas = tk.Canvas(parent, bg=_bg(widget, "#FFF8E1"), highlightthickness=0)
        inner = tk.Frame(canvas, bg=_bg(widget, "#FFF8E1"))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        if widget.children:
            _mount(inner, widget.children[0])
        canvas.pack(fill=tk.BOTH, expand=True)
        return canvas
    if isinstance(widget, Label):
        label = tk.Label(
            parent,
            text=widget.text,
            fg=widget.color,
            bg=_bg(widget, "#FFF8E1"),
            font=("Helvetica", int(widget.font_size), "bold" if widget.bold else "normal"),
            wraplength=320,
            justify=widget.halign,
        )
        widget._tk = label  # type: ignore[attr-defined]
        _watch_text(widget, label)
        return label
    if isinstance(widget, Button):
        button = tk.Button(
            parent,
            text=widget.text,
            fg=widget.color,
            bg=widget.background_color or "#F4C430",
            font=("Helvetica", int(widget.font_size), "bold"),
            command=lambda: widget.dispatch("on_press"),
        )
        widget._tk = button  # type: ignore[attr-defined]
        _watch_text(widget, button)
        return button
    if isinstance(widget, TextInput):
        var = tk.StringVar(value=widget.text)
        entry = tk.Entry(parent, textvariable=var, font=("Helvetica", int(widget.font_size)))
        def _changed(*_args: object) -> None:
            widget.text = var.get()
            widget.dispatch("on_text", widget.text)
        var.trace_add("write", _changed)
        widget._tk = entry  # type: ignore[attr-defined]
        return entry
    if isinstance(widget, (CheckBox, Switch)):
        var = tk.BooleanVar(value=widget.active)
        box = tk.Checkbutton(parent, variable=var, bg=_bg(widget, "#FFF8E1"))
        def _toggled(*_args: object) -> None:
            widget.active = bool(var.get())
            widget.dispatch("on_active", widget.active)
        var.trace_add("write", _toggled)
        return box
    if isinstance(widget, Slider):
        scale = tk.Scale(
            parent,
            from_=widget.min,
            to=widget.max,
            orient=tk.HORIZONTAL,
            bg=_bg(widget, "#FFF8E1"),
        )
        scale.set(widget.value)
        def _moved(value: str) -> None:
            widget.value = float(value)
            widget.dispatch("on_value", widget.value)
        scale.configure(command=_moved)
        return scale
    if isinstance(widget, ProgressBar):
        label = tk.Label(parent, text=f"{int(widget.value)}/{int(widget.max)}", bg=_bg(widget, "#FFF8E1"))
        return label
    frame = tk.Frame(parent, bg=_bg(widget, "#FFF8E1"))
    for child in widget.children:
        _mount(frame, child).pack()
    return frame


def _bg(widget: Widget, default: str) -> str:
    return widget.background_color or default


def _watch_text(widget: Widget, control: Any) -> None:
    original = type(widget).text if False else None  # keep linters calm
    _ = original
    current = widget.text

    def setter(instance: Widget, value: str) -> None:
        object.__setattr__(instance, "text", value)
        try:
            control.configure(text=value)
        except tk.TclError:
            pass

    # Property-style assignment from app handlers updates the preview.
    widget.__dict__["__set_text"] = setter
    widget.text = current
