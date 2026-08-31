"""Generate a .NET C# project for a BanANDa Windows app."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from bananda.transpile.converter import TranspileResult


@dataclass
class WindowsProject:
    root: Path
    app_class: str
    title: str
    project_file: Path


def generate_windows_project(
    result: TranspileResult,
    dest: str | Path,
    *,
    app_name: str | None = None,
) -> WindowsProject:
    root = Path(dest)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)

    title = app_name or result.title or "BanANDa"
    project_name = _safe_name(result.app_class or "BanandaApp")
    project_file = root / f"{project_name}.csproj"
    project_file.write_text(_csproj(title), encoding="utf-8")

    for rel, content in result.files.items():
        (root / Path(rel).name).write_text(content, encoding="utf-8")

    runtime = resources.files("bananda").joinpath("runtime/csharp")
    _copy_tree(runtime, root)

    (root / "README-WINDOWS.txt").write_text(
        f"{title}\n\n"
        "This is a BanANDa Windows app transpiled from Python to C#. "
        "There is no Python interpreter in the shipped binary.\n\n"
        "On Windows: dotnet run -p "
        f"{project_name}.csproj\n"
        "or run the published .exe after `dotnet publish -c Release -r win-x64`.\n",
        encoding="utf-8",
    )
    return WindowsProject(root=root, app_class=result.app_class, title=title, project_file=project_file)


def _safe_name(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "" for ch in name)
    return cleaned or "BanandaApp"


def _copy_tree(src, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dest / item.name
        if item.is_dir():
            _copy_tree(item, target)
        else:
            target.write_text(item.read_text(encoding="utf-8"), encoding="utf-8")


def _csproj(title: str) -> str:
    return f"""\
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <AssemblyTitle>{title}</AssemblyTitle>
    <RootNamespace>Bananda.Generated</RootNamespace>
    <DefineConstants Condition="$([MSBuild]::IsOSPlatform('Windows'))">$(DefineConstants);WINDOWS</DefineConstants>
    <UseWindowsForms Condition="$([MSBuild]::IsOSPlatform('Windows'))">true</UseWindowsForms>
    <OutputType Condition="$([MSBuild]::IsOSPlatform('Windows'))">WinExe</OutputType>
    <TargetFramework Condition="$([MSBuild]::IsOSPlatform('Windows'))">net8.0-windows</TargetFramework>
  </PropertyGroup>
</Project>
"""
