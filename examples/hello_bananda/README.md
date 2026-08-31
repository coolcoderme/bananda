# Hello BanANDa

Test application used to exercise the library.

```bash
# Widget tree on the host (no Android SDK required)
BANANDA_HEADLESS=1 python examples/hello_bananda/main.py

# Kotlin + Gradle project + debug APK
bananda build examples/hello_bananda/main.py \
    --package com.bananda.examples.hellobananda \
    --out build/android \
    --apk-out DemoApp-debug.apk
```
