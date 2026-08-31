"""Windows C# project generation and builds."""

from bananda.windows.builder import WindowsBuildResult, build_windows
from bananda.windows.project import WindowsProject, generate_windows_project

__all__ = ["WindowsBuildResult", "WindowsProject", "build_windows", "generate_windows_project"]
