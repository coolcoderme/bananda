"""Errors raised by BanANDa."""


class BanandaError(Exception):
    """Base error for the BanANDa toolkit."""


class BanandaTranspileError(BanandaError):
    """Python source could not be converted to Kotlin."""

    def __init__(self, message: str, filename: str | None = None, lineno: int | None = None):
        self.filename = filename
        self.lineno = lineno
        loc = ""
        if filename and lineno:
            loc = f"{filename}:{lineno}: "
        elif filename:
            loc = f"{filename}: "
        super().__init__(f"{loc}{message}")


class BanandaBuildError(BanandaError):
    """Android project generation or APK compilation failed."""
