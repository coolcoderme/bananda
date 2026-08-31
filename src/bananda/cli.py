"""Command-line interface: transpile BanANDa apps and compile platform binaries."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from bananda import __version__
from bananda.android.builder import build_apk
from bananda.android.project import generate_android_project
from bananda.exceptions import BanandaError
from bananda.linux.builder import build_linux
from bananda.linux.project import generate_linux_project
from bananda.targets import Target
from bananda.transpile.converter import transpile_file
from bananda.transpile.names import java_package_from_name
from bananda.windows.builder import build_windows
from bananda.windows.project import generate_windows_project


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bananda",
        description=(
            "Transpile BanANDa Python apps to the platform language: "
            "Kotlin (Android), C++ (Linux), or C# (Windows)."
        ),
    )
    parser.add_argument("--version", action="version", version=f"bananda {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("transpile", help="Convert a Python app to platform sources")
    _add_common(t, default_out="build/gen")

    p = sub.add_parser("project", help="Generate a native project for a target")
    _add_common(p, default_out="build/project")
    p.add_argument("--name", default=None, help="Application display name")

    b = sub.add_parser("build", help="Generate a project and compile it")
    _add_common(b, default_out="build/out")
    b.add_argument("--name", default=None)
    b.add_argument("--sdk", default=None, help="Android SDK root (Android target)")
    b.add_argument("--apk-out", type=Path, default=None, help="Copy the Android APK here")
    b.add_argument("--artifact-out", type=Path, default=None, help="Copy the built binary here")

    r = sub.add_parser("run", help="Build the widget tree in-process (desktop / headless)")
    r.add_argument("source", type=Path)

    args = parser.parse_args(argv)
    try:
        if args.cmd == "transpile":
            return _transpile(args)
        if args.cmd == "project":
            return _project(args)
        if args.cmd == "build":
            return _build(args)
        if args.cmd == "run":
            return _run(args)
    except BanandaError as exc:
        print(f"bananda: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"bananda: {exc}", file=sys.stderr)
        return 1
    return 0


def _add_common(parser: argparse.ArgumentParser, default_out: str) -> None:
    parser.add_argument("source", type=Path, help="Python entrypoint (e.g. main.py)")
    parser.add_argument("--out", type=Path, default=Path(default_out), help="Output directory")
    parser.add_argument("--package", default=None, help="Application package / namespace")
    parser.add_argument(
        "--target",
        default="android",
        choices=["android", "linux", "windows"],
        help="android=Kotlin, linux=C++, windows=C#",
    )


def _package_for(source: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    return java_package_from_name(source.stem)


def _transpile(args: argparse.Namespace) -> int:
    result = transpile_file(
        args.source,
        package=_package_for(args.source, args.package),
        target=args.target,
    )
    args.out.mkdir(parents=True, exist_ok=True)
    for rel, content in result.files.items():
        path = args.out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(path)
    for warning in result.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    return 0


def _project(args: argparse.Namespace) -> int:
    target = Target.parse(args.target)
    result = transpile_file(
        args.source,
        package=_package_for(args.source, args.package),
        target=target,
    )
    if target is Target.LINUX:
        project = generate_linux_project(result, args.out, app_name=args.name)
        print(project.root)
        return 0
    if target is Target.WINDOWS:
        project = generate_windows_project(result, args.out, app_name=args.name)
        print(project.root)
        return 0
    project = generate_android_project(result, args.out, app_name=args.name)
    print(project.root)
    return 0


def _build(args: argparse.Namespace) -> int:
    target = Target.parse(args.target)
    result = transpile_file(
        args.source,
        package=_package_for(args.source, args.package),
        target=target,
    )
    if target is Target.LINUX:
        project = generate_linux_project(result, args.out, app_name=args.name)
        built = build_linux(project.root)
        dest = args.artifact_out or (Path.cwd() / built.binary.name)
        dest.write_bytes(built.binary.read_bytes())
        dest.chmod(built.binary.stat().st_mode)
        print(dest)
        return 0
    if target is Target.WINDOWS:
        project = generate_windows_project(result, args.out, app_name=args.name)
        built = build_windows(project.root)
        dest = args.artifact_out or (Path.cwd() / built.assembly.name)
        dest.write_bytes(built.assembly.read_bytes())
        print(dest)
        return 0
    project = generate_android_project(result, args.out, app_name=args.name)
    built = build_apk(project.root, sdk_dir=args.sdk)
    dest = args.apk_out or args.artifact_out or (Path.cwd() / f"{result.app_class}-debug.apk")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(built.apk.read_bytes())
    print(dest)
    return 0


def _run(args: argparse.Namespace) -> int:
    import importlib.util
    import os

    os.environ.setdefault("BANANDA_HEADLESS", "1")
    spec = importlib.util.spec_from_file_location("bananda_user_app", args.source)
    if spec is None or spec.loader is None:
        raise BanandaError(f"cannot load {args.source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
