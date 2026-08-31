import pytest

from bananda.exceptions import BanandaTranspileError
from bananda.transpile import transpile_source


def kotlin(source: str) -> str:
    return transpile_source(source, filename="sample.py", package="com.example.demo").kotlin


def test_app_class_and_build_override():
    src = """
from bananda import App, Label

class Hello(App):
    title = "Hi"

    def build(self):
        return Label(text="Yo")
"""
    out = kotlin(src)
    assert "package com.example.demo" in out
    assert "class Hello : App()" in out
    assert "override var title: String = \"Hi\"" in out
    assert "override fun build(): Widget" in out
    assert 'Label(text = "Yo")' in out
    assert "import com.bananda.uix.Label" in out


def test_fstrings_methods_and_control_flow():
    src = """
from bananda import App, Label

class C(App):
    def build(self):
        self.count = 0
        return Label(text="x")

    def tick(self, instance):
        self.count += 1
        name = "Ada"
        if self.count > 0 and name:
            self.count = self.count + 1
        for i in range(3):
            self.count = self.count + i
        return f"Count: {self.count}"
"""
    out = kotlin(src)
    assert "var count: Int = 0" in out
    assert "this.count += 1" in out
    assert "var name = \"Ada\"" in out
    assert "for (i in 0 until 3)" in out
    assert '"Count: ${this.count}"' in out
    assert "fun tick(instance: Widget)" in out


def test_event_handlers_and_size_hint():
    src = """
from bananda import App, BoxLayout, Button

class C(App):
    def build(self):
        row = BoxLayout(orientation="horizontal", size_hint=(1, None), height=56)
        row.add_widget(Button(text="+1", on_press=self.increment))
        return row

    def increment(self, instance):
        pass
"""
    out = kotlin(src)
    assert "onPress = this::increment" in out
    assert "SizeHint(1.0, null)" in out
    assert "height = 56" in out
    assert "row.addWidget(" in out


def test_main_guard_is_skipped():
    src = """
from bananda import App, Label

class C(App):
    def build(self):
        return Label(text="x")

if __name__ == "__main__":
    C().run()
"""
    out = kotlin(src)
    assert "run(" not in out
    assert "__main__" not in out


def test_not_string_becomes_is_null_or_blank():
    src = """
from bananda import App, Label

class C(App):
    def build(self):
        self.name = ""
        return Label(text="x")

    def greet(self, instance):
        who = self.name.strip()
        if not who:
            who = "friend"
        return f"Hello, {who}!"
"""
    out = kotlin(src)
    assert "this.name.trim()" in out
    assert "who.isNullOrBlank()" in out
    assert '"Hello, ${who}!"' in out


def test_range_and_builtins():
    src = """
from bananda import App, Label

class C(App):
    def build(self):
        values = [1, 2, 3]
        total = 0
        for n in values:
            total = total + n
        print("sum", total, len(values))
        return Label(text=str(total))
"""
    out = kotlin(src)
    assert "mutableListOf(1, 2, 3)" in out
    assert "values.size" in out
    assert "android.util.Log.d" in out
    assert "total.toString()" in out


def test_elif_and_compare():
    src = """
from bananda import App, Label

class C(App):
    def build(self):
        x = 2
        if x < 0:
            y = "neg"
        elif x == 0:
            y = "zero"
        else:
            y = "pos"
        return Label(text=y)
"""
    out = kotlin(src)
    assert "} else if (x == 0) {" in out
    assert "} else {" in out


def test_syntax_error_has_location():
    with pytest.raises(BanandaTranspileError) as exc:
        transpile_source("def oops(:\n    pass\n", filename="bad.py")
    assert "bad.py" in str(exc.value)


def test_unsupported_syntax():
    with pytest.raises(BanandaTranspileError):
        kotlin("async def nope():\n    return 1\n")


def test_main_activity_is_emitted():
    result = transpile_source(
        "from bananda import App, Label\nclass Z(App):\n    def build(self):\n        return Label(text='z')\n",
        package="com.example.z",
    )
    activity = result.files["com/example/z/MainActivity.kt"]
    assert "class MainActivity" in activity
    assert "val application = Z()" in activity
