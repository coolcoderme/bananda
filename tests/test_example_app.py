from pathlib import Path

from bananda.transpile import transpile_file
from hello_bananda.main import DemoApp

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "hello_bananda" / "main.py"


def test_demo_app_widget_tree():
    app = DemoApp()
    root = app.build()
    labels = [w for w in root.walk() if getattr(w, "widget_type", "") == "Label"]
    buttons = [w for w in root.walk() if getattr(w, "widget_type", "") == "Button"]
    assert app.title == "BanANDa Demo"
    assert any(w.text == "BanANDa" for w in labels)
    assert [b.text for b in buttons] == ["+1", "-1", "Reset", "Greet me"]
    plus = buttons[0]
    plus.dispatch("on_press")
    plus.dispatch("on_press")
    assert app.count == 2
    assert app.counter_label.text == "Count: 2"
    buttons[2].dispatch("on_press")
    assert app.count == 0
    app.name_input.dispatch("on_text", "Ada")
    buttons[3].dispatch("on_press")
    assert app.greeting.text == "Hello, Ada! Count is 0."


def test_demo_app_transpiles_to_kotlin():
    result = transpile_file(EXAMPLE, package="com.bananda.examples.hellobananda")
    kotlin = result.kotlin
    assert result.app_class == "DemoApp"
    assert "class DemoApp : App()" in kotlin
    assert "onPress = this::increment" in kotlin
    assert "onPress = this::decrement" in kotlin
    assert "onText = this::onName" in kotlin
    assert "fun _refreshCounter()" in kotlin
    assert '"Count: ${this.count}"' in kotlin
    assert "this.name.trim()" in kotlin
    assert "who.isNullOrBlank()" in kotlin
    activity = result.files["com/bananda/examples/hellobananda/MainActivity.kt"]
    assert "DemoApp()" in activity
