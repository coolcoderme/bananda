"""Python identifier and BanANDa API name mapping to Kotlin."""

from __future__ import annotations

WIDGET_TYPES = {
    "App",
    "Widget",
    "BoxLayout",
    "GridLayout",
    "ScrollView",
    "Label",
    "Button",
    "TextInput",
    "CheckBox",
    "Switch",
    "Slider",
    "ProgressBar",
}

API_NAMES = {
    "add_widget": "addWidget",
    "remove_widget": "removeWidget",
    "clear_widgets": "clearWidgets",
    "font_size": "fontSize",
    "on_press": "onPress",
    "on_text": "onText",
    "on_active": "onActive",
    "on_value": "onValue",
    "hint_text": "hintText",
    "size_hint": "sizeHint",
    "background_color": "backgroundColor",
    "on_start": "onStart",
    "on_stop": "onStop",
    "on_pause": "onPause",
    "on_resume": "onResume",
    "text_color": "color",
    "halign": "halign",
    "strip": "trim",
    "lstrip": "trimStart",
    "rstrip": "trimEnd",
    "upper": "uppercase",
    "lower": "lowercase",
    "startswith": "startsWith",
    "endswith": "endsWith",
    "append": "add",
    "extend": "addAll",
    "find": "indexOf",
}

OVERRIDE_METHODS = {
    "build": "build",
    "on_start": "onStart",
    "on_stop": "onStop",
    "on_pause": "onPause",
    "on_resume": "onResume",
}

BANANDA_MODULES = {
    "bananda",
    "bananda.app",
    "bananda.uix",
    "bananda.uix.widget",
    "bananda.uix.layouts",
    "bananda.uix.labels",
    "bananda.uix.buttons",
    "bananda.uix.inputs",
    "bananda.properties",
}


def to_camel(name: str) -> str:
    """Convert a Python identifier to Kotlin camelCase, honoring BanANDa API names."""
    if name in API_NAMES:
        return API_NAMES[name]
    if name in OVERRIDE_METHODS:
        return OVERRIDE_METHODS[name]
    if name in WIDGET_TYPES or name[:1].isupper():
        return name
    prefix = ""
    working = name
    while working.startswith("_"):
        prefix += "_"
        working = working[1:]
    if not working:
        return name
    parts = working.split("_")
    camel = parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:] if part)
    return prefix + camel


def kotlin_package(python_package: str) -> str:
    return python_package


def java_package_from_name(app_name: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "" for ch in app_name)
    if not slug:
        slug = "app"
    return f"com.bananda.apps.{slug}"
