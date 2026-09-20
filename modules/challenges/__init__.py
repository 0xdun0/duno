"""modules/challenges/__init__.py — Blueprint do Módulo CTF Challenges (lazy loading)."""


def __getattr__(name):
    if name == "bp":
        from modules.challenges.routes import bp
        return bp
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["bp"]
