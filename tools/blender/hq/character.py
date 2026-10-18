"""Proxy for the character being built (caveman = Rock Slinger, ugo = Ugo). Shared modules import this and
read attributes from whichever character module `use()` selected."""
import importlib

_mod = None
NAME = "caveman"


def use(name):
    global _mod, NAME
    _mod = importlib.import_module(name)
    NAME = name
    return _mod


def module():
    global _mod
    if _mod is None:
        use(NAME)
    return _mod


def __getattr__(attr):
    return getattr(module(), attr)
