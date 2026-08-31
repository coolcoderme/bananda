# BanANDa

Write apps in Python with a [Kivy](https://kivy.org)-style widget API. BanANDa does **not** ship a Python interpreter in the final binary. It transpiles your Python to the platform language, then compiles that:

| Target | Language | Output |
| --- | --- | --- |
| Android | Kotlin | APK |
| Linux | C++ | native ELF (GTK 3 when available) |
| Windows | C# | .NET assembly / WinForms `.exe` |

```
Python (BanANDa widgets)
   ├── android → Kotlin + AndroidX views → APK
   ├── linux   → C++ + GTK 3             → ELF
   └── windows → C# + WinForms           → exe/dll
```

## Install

```bash
pip install -e ".[dev]"
```

You need Python 3.10+ plus the toolchain for each target you compile:

- **Android:** JDK 17+ and the Android SDK (`ANDROID_SDK_ROOT`)
- **Linux:** `g++`, CMake, and optionally `libgtk-3-dev`
- **Windows:** .NET 8 SDK (`dotnet`)

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

`python main.py` is a development preview only (Tk when a display is available). Shipping builds never embed that interpreter.

## Transpile and compile

```bash
# Android (Kotlin → APK)
bananda build examples/hello_bananda/main.py --target android \
    --package com.bananda.examples.hellobananda --apk-out DemoApp-debug.apk

# Linux (C++ → native binary)
bananda build examples/hello_bananda/main.py --target linux \
    --package com.bananda.examples.hellobananda --artifact-out DemoApp

# Windows (C# → .NET assembly)
bananda build examples/hello_bananda/main.py --target windows \
    --package com.bananda.examples.hellobananda --artifact-out DemoApp.dll
```

`bananda transpile --target linux|windows|android` writes sources only. `bananda project` writes a CMake, `.csproj`, or Gradle tree you can open in an IDE.

Set `BANANDA_HEADLESS=1` to print the widget tree from a Linux or Windows build instead of opening a window.

## What is supported

The transpilers walk the Python AST for a focused subset:

- `App` subclasses and `build` / lifecycle overrides
- Widgets: `BoxLayout`, `GridLayout`, `ScrollView`, `Label`, `Button`, `TextInput`, `CheckBox`, `Switch`, `Slider`, `ProgressBar`
- Event kwargs (`on_press`, `on_text`, …) and `.bind()`
- Assignments, `if`/`elif`/`else`, `for`/`while`, f-strings, lists/dicts, and common builtins

Unsupported syntax raises `BanandaTranspileError` with a file location.

## Test application

`examples/hello_bananda/main.py` is the bundled demo: a counter, a name field, and a greeting. Tests cover the live Python widget tree, Kotlin/C++/C# output, generated projects, and compiled Android/Linux/Windows artifacts when the matching SDK is present.

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT. See `LICENSE`.
