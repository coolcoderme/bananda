from pathlib import Path

from bananda.cli import main
from bananda.linux.project import generate_linux_project
from bananda.transpile import transpile_file
from bananda.windows.project import generate_windows_project

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "hello_bananda" / "main.py"


def test_linux_transpile_is_cpp():
    result = transpile_file(EXAMPLE, package="com.bananda.examples.hellobananda", target="linux")
    cpp = next(iter(result.files.values()))
    assert result.target.value == "linux"
    assert "class DemoApp : public bananda::App" in cpp
    assert "bananda::Widget* build() override" in cpp
    assert "new bananda::BoxLayout()" in cpp
    assert "new bananda::Button()" in cpp
    assert "root->addWidget" in cpp
    assert "this->counterLabel->text" in cpp
    assert "int main()" in cpp
    assert "MainActivity" not in cpp
    assert "package com." not in cpp


def test_windows_transpile_is_csharp():
    result = transpile_file(EXAMPLE, package="com.bananda.examples.hellobananda", target="windows")
    csharp = result.files["DemoApp.cs"]
    assert result.target.value == "windows"
    assert "public class DemoApp : App" in csharp
    assert "public override Widget Build()" in csharp
    assert "new Button" in csharp
    assert "OnPress = Increment" in csharp
    assert "this.Name.Trim()" in csharp
    assert "string.IsNullOrWhiteSpace(who)" in csharp
    assert "class MainActivity" not in csharp
    assert "fun main" not in csharp
    program = result.files["Program.cs"]
    assert "new DemoApp().Start()" in program


def test_generate_linux_project(tmp_path: Path):
    result = transpile_file(EXAMPLE, package="com.bananda.examples.hellobananda", target="linux")
    project = generate_linux_project(result, tmp_path / "linux", app_name="BanANDa Demo")
    assert (project.root / "CMakeLists.txt").is_file()
    assert (project.root / "src" / "DemoApp.cpp").is_file()
    assert (project.root / "include" / "bananda" / "runtime.hpp").is_file()
    cmake = (project.root / "CMakeLists.txt").read_text(encoding="utf-8")
    assert "gtk+-3.0" in cmake


def test_generate_windows_project(tmp_path: Path):
    result = transpile_file(EXAMPLE, package="com.bananda.examples.hellobananda", target="windows")
    project = generate_windows_project(result, tmp_path / "windows", app_name="BanANDa Demo")
    assert project.project_file.is_file()
    assert (project.root / "DemoApp.cs").is_file()
    assert (project.root / "Program.cs").is_file()
    assert (project.root / "Bananda" / "Runtime.cs").is_file()
    csproj = project.project_file.read_text(encoding="utf-8")
    assert "UseWindowsForms" in csproj


def test_cli_transpile_linux_and_windows(tmp_path: Path):
    linux_out = tmp_path / "cpp"
    windows_out = tmp_path / "cs"
    assert main(["transpile", str(EXAMPLE), "--target", "linux", "--out", str(linux_out), "--package", "com.demo.app"]) == 0
    assert any(path.suffix == ".cpp" for path in linux_out.rglob("*"))
    assert main(["transpile", str(EXAMPLE), "--target", "windows", "--out", str(windows_out), "--package", "com.demo.app"]) == 0
    assert (windows_out / "DemoApp.cs").is_file()
    assert (windows_out / "Program.cs").is_file()
