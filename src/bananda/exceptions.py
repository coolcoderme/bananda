"""Errors raised by BanANDa."""


class BanandaError(Exception):
    """Base error for the BanANDa toolkit."""


class BanandaTranspileError(BanandaError):
    """Python source could not be converted to the target language."""

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
    """Project generation or native compilation failed."""
