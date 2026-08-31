"""Compile a generated Windows C# project with the .NET SDK."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from bananda.exceptions import BanandaBuildError
from bananda.tooling import find_dotnet


@dataclass
class WindowsBuildResult:
    assembly: Path
    project: Path
    log: str


def build_windows(
    project_root: str | Path,
    *,
    dotnet: str | None = None,
    timeout: int = 600,
) -> WindowsBuildResult:
    root = Path(project_root)
    csproj = next(root.glob("*.csproj"), None)
    if csproj is None:
        raise BanandaBuildError(f"no .csproj in {root}")
    dotnet_bin = dotnet or find_dotnet()
    env = os.environ.copy()
    env.setdefault("DOTNET_ROOT", str(Path(dotnet_bin).resolve().parent))
    env.setdefault("DOTNET_CLI_TELEMETRY_OPTOUT", "1")
    proc = subprocess.run(
        [dotnet_bin, "build", str(csproj), "-c", "Release", "--nologo"],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
        cwd=root,
    )
    log = (proc.stdout or "") + "\n" + (proc.stderr or "")
    assembly = _find_assembly(root)
    if proc.returncode != 0 or assembly is None:
        raise BanandaBuildError(f"Windows C# build failed (exit {proc.returncode}).\n{log[-4000:]}")
    return WindowsBuildResult(assembly=assembly, project=root, log=log)


def _find_assembly(root: Path) -> Path | None:
    matches = sorted(root.joinpath("bin").rglob("*.dll"))
    # Prefer the app dll over Bananda runtime if both exist; the SDK-style
    # project compiles everything into one assembly named after the csproj.
    csproj = next(root.glob("*.csproj"), None)
    if csproj:
        named = [path for path in matches if path.stem == csproj.stem]
        if named:
            return named[-1]
    return matches[-1] if matches else None
