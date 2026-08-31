"""Generate a complete Gradle Android project around transpiled Kotlin."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from bananda.transpile.converter import TranspileResult
from bananda.transpile.names import java_package_from_name


@dataclass
class AndroidProject:
    root: Path
    package: str
    app_class: str
    title: str

    @property
    def app_dir(self) -> Path:
        return self.root / "app"


def generate_android_project(
    result: TranspileResult,
    dest: str | Path,
    *,
    app_name: str | None = None,
    version: str = "1.0.0",
    version_code: int = 1,
    min_sdk: int = 24,
    target_sdk: int = 34,
) -> AndroidProject:
    root = Path(dest)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)

    package = result.package
    title = app_name or result.title or "BanANDa"
    application_id = package if package.startswith("com.") else java_package_from_name(title)

    (root / "settings.gradle.kts").write_text(_SETTINGS, encoding="utf-8")
    (root / "build.gradle.kts").write_text(_ROOT_BUILD, encoding="utf-8")
    (root / "gradle.properties").write_text(_GRADLE_PROPERTIES, encoding="utf-8")
    (root / "gradle" / "wrapper").mkdir(parents=True)
    (root / "gradle" / "wrapper" / "gradle-wrapper.properties").write_text(
        _WRAPPER_PROPERTIES, encoding="utf-8"
    )

    app = root / "app"
    src_main = app / "src" / "main"
    java_root = src_main / "java"
    res = src_main / "res"
    (res / "values").mkdir(parents=True)
    (res / "drawable").mkdir(parents=True)
    (res / "mipmap-anydpi-v26").mkdir(parents=True)
    java_root.mkdir(parents=True)

    (app / "build.gradle.kts").write_text(
        _app_build(application_id, version, version_code, min_sdk, target_sdk),
        encoding="utf-8",
    )
    (src_main / "AndroidManifest.xml").write_text(
        _manifest(package, title),
        encoding="utf-8",
    )
    (res / "values" / "strings.xml").write_text(_strings(title), encoding="utf-8")
    (res / "values" / "colors.xml").write_text(_COLORS, encoding="utf-8")
    (res / "values" / "themes.xml").write_text(_THEMES, encoding="utf-8")
    (res / "drawable" / "ic_launcher_foreground.xml").write_text(_ICON, encoding="utf-8")
    (res / "drawable" / "ic_launcher_background.xml").write_text(_ICON_BG, encoding="utf-8")
    (res / "mipmap-anydpi-v26" / "ic_launcher.xml").write_text(_ADAPTIVE, encoding="utf-8")

    _copy_runtime(java_root)
    for rel, content in result.files.items():
        path = java_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    return AndroidProject(root=root, package=package, app_class=result.app_class, title=title)


def _copy_runtime(java_root: Path) -> None:
    runtime = resources.files("bananda").joinpath("runtime/kotlin")
    _copy_tree(runtime, java_root)


def _copy_tree(src, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dest / item.name
        if item.is_dir():
            _copy_tree(item, target)
        else:
            target.write_text(item.read_text(encoding="utf-8"), encoding="utf-8")


_SETTINGS = """\
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "BanandaApp"
include(":app")
"""

_ROOT_BUILD = """\
plugins {
    id("com.android.application") version "8.7.3" apply false
    id("org.jetbrains.kotlin.android") version "2.0.21" apply false
}
"""

_GRADLE_PROPERTIES = """\
org.gradle.jvmargs=-Xmx2g -Dfile.encoding=UTF-8
android.useAndroidX=true
kotlin.code.style=official
android.nonTransitiveRClass=true
"""

_WRAPPER_PROPERTIES = """\
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-8.10.2-bin.zip
networkTimeout=10000
validateDistributionUrl=true
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
"""


def _app_build(application_id: str, version: str, version_code: int, min_sdk: int, target_sdk: int) -> str:
    return f"""\
plugins {{
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}}

android {{
    namespace = "{application_id}"
    compileSdk = {target_sdk}

    defaultConfig {{
        applicationId = "{application_id}"
        minSdk = {min_sdk}
        targetSdk = {target_sdk}
        versionCode = {version_code}
        versionName = "{version}"
    }}

    buildTypes {{
        release {{
            isMinifyEnabled = false
        }}
        debug {{
            isMinifyEnabled = false
        }}
    }}

    compileOptions {{
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }}
    kotlinOptions {{
        jvmTarget = "17"
    }}
}}

dependencies {{
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("com.google.android.material:material:1.12.0")
}}
"""


def _manifest(package: str, title: str) -> str:
    return f"""\
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:theme="@style/Theme.Bananda">
        <activity
            android:name="{package}.MainActivity"
            android:exported="true"
            android:label="@string/app_name"
            android:theme="@style/Theme.Bananda">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""


def _strings(title: str) -> str:
    safe = (
        title.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    return f"""\
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">{safe}</string>
</resources>
"""


_COLORS = """\
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="bananda_yellow">#F4C430</color>
    <color name="bananda_cream">#FFF8E1</color>
    <color name="bananda_brown">#3D2E00</color>
</resources>
"""

_THEMES = """\
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.Bananda" parent="Theme.MaterialComponents.DayNight.NoActionBar">
        <item name="colorPrimary">@color/bananda_yellow</item>
        <item name="colorPrimaryVariant">@color/bananda_brown</item>
        <item name="colorOnPrimary">@color/bananda_brown</item>
        <item name="android:statusBarColor">@color/bananda_yellow</item>
        <item name="android:windowBackground">@color/bananda_cream</item>
    </style>
</resources>
"""

_ICON = """\
<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path
        android:fillColor="#3D2E00"
        android:pathData="M54,22c8,0 18,10 22,28 3,14 -2,28 -12,34 -8,5 -18,5 -26,0 -10,-6 -15,-20 -12,-34 4,-18 14,-28 28,-28z"/>
    <path
        android:fillColor="#F4C430"
        android:pathData="M54,28c6,0 14,8 17,23 2,12 -2,23 -10,28 -6,4 -14,4 -20,0 -8,-5 -12,-16 -10,-28 3,-15 11,-23 23,-23z"/>
</vector>
"""

_ICON_BG = """\
<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path
        android:fillColor="#FFF8E1"
        android:pathData="M0,0h108v108h-108z"/>
</vector>
"""

_ADAPTIVE = """\
<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@drawable/ic_launcher_background"/>
    <foreground android:drawable="@drawable/ic_launcher_foreground"/>
</adaptive-icon>
"""
