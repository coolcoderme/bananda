"""Shared lookup for Gradle and the JDK."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def find_gradle() -> str:
    for candidate in (
        os.environ.get("BANANDA_GRADLE"),
        shutil.which("gradle"),
        str(Path.home() / "gradle-dist" / "gradle-8.10.2" / "bin" / "gradle"),
        "/home/ubuntu/gradle-dist/gradle-8.10.2/bin/gradle",
    ):
        if candidate and Path(candidate).exists():
            return candidate
    return "gradle"


def find_cmake() -> str:
    return shutil.which("cmake") or "cmake"


def find_dotnet() -> str:
    for candidate in (
        os.environ.get("BANANDA_DOTNET"),
        shutil.which("dotnet"),
        str(Path.home() / ".dotnet" / "dotnet"),
        "/home/ubuntu/.dotnet/dotnet",
    ):
        if candidate and Path(candidate).exists():
            return candidate
    return "dotnet"


def java_home() -> str:
    if os.environ.get("JAVA_HOME"):
        return os.environ["JAVA_HOME"]
    java = shutil.which("java")
    if java:
        real = Path(java).resolve()
        if real.parent.name == "bin":
            return str(real.parent.parent)
    return "/usr/lib/jvm/java-21-openjdk-amd64"
