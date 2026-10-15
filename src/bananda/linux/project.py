"""Generate a CMake C++ project for a BanANDa Linux app."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from bananda.transpile.converter import TranspileResult


@dataclass
class LinuxProject:
    root: Path
    app_class: str
    title: str
    binary_name: str


def generate_linux_project(
    result: TranspileResult,
    dest: str | Path,
    *,
    app_name: str | None = None,
) -> LinuxProject:
    root = Path(dest)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    src = root / "src"
    include = root / "include"
    src.mkdir()
    include.mkdir()

    title = app_name or result.title or "BanANDa"
    binary = _safe_name(result.app_class or "BanandaApp")

    for rel, content in result.files.items():
        (src / Path(rel).name).write_text(content, encoding="utf-8")

    runtime_src = resources.files("bananda").joinpath("runtime/cpp/bananda")
    dest_runtime = include / "bananda"
    dest_runtime.mkdir(parents=True)
    for item in runtime_src.iterdir():
        if item.is_file():
            (dest_runtime / item.name).write_text(item.read_text(encoding="utf-8"), encoding="utf-8")

    (root / "CMakeLists.txt").write_text(_cmake(binary, title), encoding="utf-8")
    (root / f"{binary}.desktop").write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={title}\n"
        f"Exec={binary}\n"
        "Terminal=false\n"
        "Categories=Utility;\n",
        encoding="utf-8",
    )
    return LinuxProject(root=root, app_class=result.app_class, title=title, binary_name=binary)


def _safe_name(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "" for ch in name)
    return cleaned or "BanandaApp"


def _cmake(binary: str, title: str) -> str:
    return f"""\
cmake_minimum_required(VERSION 3.16)
project({binary} LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

file(GLOB APP_SOURCES CONFIGURE_DEPENDS "${{CMAKE_SOURCE_DIR}}/src/*.cpp")

add_executable({binary} ${{APP_SOURCES}})
target_include_directories({binary} PRIVATE "${{CMAKE_SOURCE_DIR}}/include")
target_compile_definitions({binary} PRIVATE BANANDA_APP_TITLE="{title}")

find_package(PkgConfig)
if (PkgConfig_FOUND)
    pkg_check_modules(GTK3 gtk+-3.0)
endif()
if (GTK3_FOUND)
    target_compile_definitions({binary} PRIVATE BANANDA_HAS_GTK=1)
    target_include_directories({binary} PRIVATE ${{GTK3_INCLUDE_DIRS}})
    target_link_libraries({binary} PRIVATE ${{GTK3_LIBRARIES}})
endif()
"""
