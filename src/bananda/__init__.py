"""BanANDa: write apps in Python, ship Kotlin/C++/C# — no interpreter in the binary."""

from bananda.app import App
from bananda.uix.buttons import Button
from bananda.uix.inputs import CheckBox, Slider, Switch, TextInput
from bananda.uix.labels import Label, ProgressBar
from bananda.uix.layouts import BoxLayout, GridLayout, ScrollView
from bananda.uix.widget import Widget

__version__ = "0.1.0"

__all__ = [
    "App",
    "BoxLayout",
    "Button",
    "CheckBox",
    "GridLayout",
    "Label",
    "ProgressBar",
    "ScrollView",
    "Slider",
    "Switch",
    "TextInput",
    "Widget",
    "__version__",
]
