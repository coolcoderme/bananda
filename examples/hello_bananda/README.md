# Hello BanANDa

Test application used to exercise the library.

```bash
# Widget tree on the host (no Android SDK required)
BANANDA_HEADLESS=1 python examples/hello_bananda/main.py

# Android APK (Kotlin)
bananda build examples/hello_bananda/main.py --target android \
    --package com.bananda.examples.hellobananda --apk-out DemoApp-debug.apk

# Linux ELF (C++)
bananda build examples/hello_bananda/main.py --target linux \
    --package com.bananda.examples.hellobananda --artifact-out DemoApp

# Windows C# assembly
bananda build examples/hello_bananda/main.py --target windows \
    --package com.bananda.examples.hellobananda --artifact-out DemoApp.dll
```
