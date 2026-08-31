# BanANDa

Write Android apps in Python with a [Kivy](https://kivy.org)-style widget API. BanANDa does **not** ship a Python interpreter inside the APK. It converts your Python to Kotlin, then compiles that Kotlin with the Android Gradle Plugin.

```
Python (BanANDa widgets)  →  Kotlin + BanANDa runtime  →  debug/release APK
```

## Install

```bash
pip install -e .
```

You need Python 3.10+, a JDK 17+, and (for APK builds) the Android SDK.

## Write an app

```python
from bananda import App, BoxLayout, Button, Label

class CounterApp(App):
    title = "Counter"

    def build(self):
        self.count = 0
        root = BoxLayout(orientation="vertical", padding=24, spacing=16)
        self.label = Label(text="Count: 0", font_size=28)
        root.add_widget(self.label)
        root.add_widget(Button(text="+1", on_press=self.increment))
        return root

    def increment(self, instance):
        self.count += 1
        self.label.text = f"Count: {self.count}"

if __name__ == "__main__":
    CounterApp().run()
```

`python main.py` builds the widget tree on the desktop (Tk preview when a display is available; otherwise it prints the tree). That path is for development only.

## Produce Kotlin and an APK

```bash
# Kotlin only
bananda transpile examples/hello_bananda/main.py --out build/kotlin \
    --package com.bananda.examples.hellobananda

# Gradle Android project (runtime + generated sources)
bananda project examples/hello_bananda/main.py --out build/android \
    --package com.bananda.examples.hellobananda

# Compile a debug APK (requires ANDROID_SDK_ROOT)
bananda build examples/hello_bananda/main.py --out build/android \
    --package com.bananda.examples.hellobananda --apk-out DemoApp-debug.apk
```

## What is supported

The transpiler walks the Python AST and emits Kotlin for a focused subset:

- `App` subclasses and `build` / lifecycle overrides
- Widgets: `BoxLayout`, `GridLayout`, `ScrollView`, `Label`, `Button`, `TextInput`, `CheckBox`, `Switch`, `Slider`, `ProgressBar`
- Event kwargs (`on_press`, `on_text`, …) and `.bind()`
- Assignments, `if`/`elif`/`else`, `for`/`while`, f-strings, lists/dicts, and common builtins (`len`, `str`, `range`, `print`)

Unsupported syntax (async, `with`, exotic unpacking, …) raises `BanandaTranspileError` with a file location.

The Kotlin runtime is a thin wrapper over AndroidX / Material views. The generated `MainActivity` attaches your `App` subclass and sets the content view from `build()`.

## Test application

`examples/hello_bananda/main.py` is the bundled demo: a counter, a name field, and a greeting. Tests exercise the live Python widget tree, the Kotlin that BanANDa emits for that file, the generated Gradle project, and — when an Android SDK is present — a real `assembleDebug` APK.

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT. See `LICENSE`.
