"""Compile a generated Linux C++ project with CMake."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from bananda.exceptions import BanandaBuildError
from bananda.tooling import find_cmake


@dataclass
class LinuxBuildResult:
    binary: Path
    project: Path
    log: str


def build_linux(
    project_root: str | Path,
    *,
    cmake: str | None = None,
    timeout: int = 600,
) -> LinuxBuildResult:
    root = Path(project_root)
    build_dir = root / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    cmake_bin = cmake or find_cmake()
    env = os.environ.copy()
    configure = subprocess.run(
        [
            cmake_bin,
            "-S",
            str(root),
            "-B",
            str(build_dir),
            "-DCMAKE_BUILD_TYPE=Release",
            "-DCMAKE_CXX_COMPILER=g++",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )
    compile_proc = subprocess.run(
        [cmake_bin, "--build", str(build_dir), "--parallel"],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )
    log = (configure.stdout or "") + (configure.stderr or "") + (compile_proc.stdout or "") + (compile_proc.stderr or "")
    binary = _find_binary(build_dir)
    if configure.returncode != 0 or compile_proc.returncode != 0 or binary is None:
        raise BanandaBuildError(f"Linux C++ build failed.\n{log[-4000:]}")
    return LinuxBuildResult(binary=binary, project=root, log=log)


def _find_binary(build_dir: Path) -> Path | None:
    candidates = [path for path in build_dir.iterdir() if path.is_file() and os.access(path, os.X_OK) and path.suffix == ""]
    if candidates:
        return sorted(candidates)[0]
    return None
