from pathlib import Path

from bananda.android.project import generate_android_project
from bananda.cli import main
from bananda.transpile import transpile_file

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "hello_bananda" / "main.py"


def test_generate_android_project(tmp_path: Path):
    result = transpile_file(EXAMPLE, package="com.bananda.examples.hellobananda")
    project = generate_android_project(result, tmp_path / "android", app_name="BanANDa Demo")
    root = project.root
    assert (root / "settings.gradle.kts").is_file()
    assert (root / "app" / "build.gradle.kts").is_file()
    assert (root / "app" / "src" / "main" / "AndroidManifest.xml").is_file()
    kotlin_root = root / "app" / "src" / "main" / "java"
    assert (kotlin_root / "com" / "bananda" / "app" / "App.kt").is_file()
    assert (kotlin_root / "com" / "bananda" / "uix" / "Button.kt").is_file()
    assert (kotlin_root / "com" / "bananda" / "examples" / "hellobananda" / "DemoApp.kt").is_file()
    assert (kotlin_root / "com" / "bananda" / "examples" / "hellobananda" / "MainActivity.kt").is_file()
    manifest = (root / "app" / "src" / "main" / "AndroidManifest.xml").read_text(encoding="utf-8")
    assert "com.bananda.examples.hellobananda.MainActivity" in manifest
    gradle = (root / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert 'applicationId = "com.bananda.examples.hellobananda"' in gradle


def test_cli_transpile(tmp_path: Path, capsys):
    out = tmp_path / "kt"
    assert main(["transpile", str(EXAMPLE), "--out", str(out), "--package", "com.bananda.examples.hellobananda"]) == 0
    printed = capsys.readouterr().out
    assert "DemoApp.kt" in printed
    text = (out / "com" / "bananda" / "examples" / "hellobananda" / "DemoApp.kt").read_text(encoding="utf-8")
    assert "class DemoApp : App()" in text


def test_cli_project(tmp_path: Path):
    dest = tmp_path / "proj"
    assert main(["project", str(EXAMPLE), "--out", str(dest), "--package", "com.demo.app"]) == 0
    assert (dest / "app" / "src" / "main" / "java" / "com" / "bananda" / "uix" / "Label.kt").is_file()
