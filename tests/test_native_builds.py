"""Compile the Hello BanANDa test app to a Linux ELF and a C# assembly."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from bananda.linux.builder import build_linux
from bananda.linux.project import generate_linux_project
from bananda.transpile import transpile_file
from bananda.windows.builder import build_windows
from bananda.windows.project import generate_windows_project

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "hello_bananda" / "main.py"


@pytest.mark.skipif(shutil.which("cmake") is None or shutil.which("g++") is None, reason="CMake/g++ not installed")
def test_linux_cpp_binary_runs_headless(tmp_path: Path):
    result = transpile_file(EXAMPLE, package="com.bananda.examples.hellobananda", target="linux")
    project = generate_linux_project(result, tmp_path / "linux", app_name="BanANDa Demo")
    built = build_linux(project.root)
    assert built.binary.is_file()
    output = subprocess.check_output(
        [str(built.binary)],
        env={**os.environ, "BANANDA_HEADLESS": "1"},
        text=True,
    )
    assert "BoxLayout" in output
    assert "BanANDa" in output
    assert "Count: 0" in output
    assert "Greet me" in output


@pytest.mark.skipif(not Path.home().joinpath(".dotnet/dotnet").exists() and shutil.which("dotnet") is None, reason=".NET SDK not installed")
def test_windows_csharp_assembly_runs_headless(tmp_path: Path):
    result = transpile_file(EXAMPLE, package="com.bananda.examples.hellobananda", target="windows")
    project = generate_windows_project(result, tmp_path / "windows", app_name="BanANDa Demo")
    built = build_windows(project.root)
    assert built.assembly.is_file()
    assert built.assembly.suffix == ".dll"
    dotnet = shutil.which("dotnet") or str(Path.home() / ".dotnet" / "dotnet")
    output = subprocess.check_output(
        [dotnet, str(built.assembly)],
        env={**os.environ, "BANANDA_HEADLESS": "1", "DOTNET_ROOT": str(Path(dotnet).resolve().parent)},
        text=True,
    )
    assert "BoxLayout" in output
    assert "BanANDa" in output
    assert "Count: 0" in output
