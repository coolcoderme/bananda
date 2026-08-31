"""Compile a generated Android project into a debug APK."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from bananda.exceptions import BanandaBuildError


@dataclass
class ApkBuildResult:
    apk: Path
    project: Path
    log: str


def build_apk(
    project_root: str | Path,
    *,
    sdk_dir: str | Path | None = None,
    gradle: str | None = None,
    timeout: int = 1800,
) -> ApkBuildResult:
    root = Path(project_root)
    sdk = Path(sdk_dir or os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME") or "")
    if not sdk or not sdk.exists():
        raise BanandaBuildError(
            "Android SDK not found. Set ANDROID_SDK_ROOT or pass sdk_dir= to build_apk()."
        )
    (root / "local.properties").write_text(f"sdk.dir={_escape_prop(sdk)}\n", encoding="utf-8")

    gradle_bin = gradle or _find_gradle()
    env = os.environ.copy()
    env["ANDROID_SDK_ROOT"] = str(sdk)
    env["ANDROID_HOME"] = str(sdk)
    env.setdefault("JAVA_HOME", _java_home())

    command = [gradle_bin, "--no-daemon", "assembleDebug"]
    try:
        proc = subprocess.run(
            command,
            cwd=root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise BanandaBuildError(f"Gradle executable not found: {gradle_bin}") from exc
    except subprocess.TimeoutExpired as exc:
        raise BanandaBuildError(f"Gradle timed out after {timeout}s") from exc

    log = (proc.stdout or "") + "\n" + (proc.stderr or "")
    apk = _find_apk(root)
    if proc.returncode != 0 or apk is None:
        raise BanandaBuildError(
            f"Gradle assembleDebug failed (exit {proc.returncode}).\n{log[-4000:]}"
        )
    return ApkBuildResult(apk=apk, project=root, log=log)


def _find_apk(root: Path) -> Path | None:
    matches = sorted((root / "app" / "build" / "outputs" / "apk").rglob("*.apk"))
    return matches[0] if matches else None


def _find_gradle() -> str:
    for candidate in (
        os.environ.get("BANANDA_GRADLE"),
        shutil.which("gradle"),
        str(Path.home() / "gradle-dist" / "gradle-8.10.2" / "bin" / "gradle"),
        "/home/ubuntu/gradle-dist/gradle-8.10.2/bin/gradle",
    ):
        if candidate and Path(candidate).exists():
            return candidate
    return "gradle"


def _java_home() -> str:
    if os.environ.get("JAVA_HOME"):
        return os.environ["JAVA_HOME"]
    java = shutil.which("java")
    if java:
        real = Path(java).resolve()
        # /usr/bin/java → /usr/lib/jvm/.../bin/java
        if real.parent.name == "bin":
            return str(real.parent.parent)
    return "/usr/lib/jvm/java-21-openjdk-amd64"


def _escape_prop(path: Path) -> str:
    return str(path).replace("\\", "\\\\").replace(":", "\\:")
