"""End-to-end APK compilation for the BanANDa test application.

Skipped automatically when the Android SDK is not installed.
"""

from __future__ import annotations

import os
import zipfile
from pathlib import Path

import pytest

from bananda.android.builder import build_apk
from bananda.android.project import generate_android_project
from bananda.exceptions import BanandaBuildError
from bananda.transpile import transpile_file

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "hello_bananda" / "main.py"


def _sdk_root() -> Path | None:
    for key in ("ANDROID_SDK_ROOT", "ANDROID_HOME"):
        value = os.environ.get(key)
        if value and Path(value).exists():
            return Path(value)
    fallback = Path.home() / "android-sdk"
    if fallback.exists():
        return fallback
    return None


@pytest.mark.skipif(_sdk_root() is None, reason="Android SDK is not installed")
def test_example_app_builds_debug_apk(tmp_path: Path):
    result = transpile_file(EXAMPLE, package="com.bananda.examples.hellobananda")
    project = generate_android_project(result, tmp_path / "android", app_name="BanANDa Demo")
    try:
        built = build_apk(project.root, sdk_dir=_sdk_root())
    except BanandaBuildError as exc:
        pytest.fail(str(exc))
    assert built.apk.is_file()
    assert built.apk.stat().st_size > 10_000
    with zipfile.ZipFile(built.apk) as archive:
        names = archive.namelist()
    assert "AndroidManifest.xml" in names
    assert any(name.startswith("classes") and name.endswith(".dex") for name in names)
