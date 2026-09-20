"""modules/kids/__init__.py — Inicializador do módulo educacional gamificado DUNO Kids."""


def __getattr__(name):
    if name == "bp":
        from modules.kids.routes import bp
        return bp
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["bp"]
