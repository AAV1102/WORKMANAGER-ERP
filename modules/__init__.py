"""
helpers to locate and register blueprints automatically.
"""

from __future__ import annotations

import importlib
import pkgutil
from flask import Blueprint

__all__ = ["iter_blueprints", "register_blueprints"]


def iter_module_blueprints():
    """
    Iterate every module/package inside :mod:`modules` to collect Blueprint objects.
    """
    package = __name__
    seen_modules = set()
    for finder, name, ispkg in pkgutil.iter_modules(__path__):
        if name in seen_modules or name.startswith("_") or not name.isidentifier():
            continue
        seen_modules.add(name)
        module = importlib.import_module(f"{package}.{name}")
        for attr_name in dir(module):
            attr_value = getattr(module, attr_name)
            if isinstance(attr_value, Blueprint):
                yield attr_value


def iter_blueprints():
    """
    Yield all unique blueprints found under :mod:`modules`.
    """
    seen_blueprints = set()
    for bp in iter_module_blueprints():
        if bp in seen_blueprints:
            continue
        seen_blueprints.add(bp)
        yield bp


def register_blueprints(app):
    """
    Register every blueprint found under :mod:`modules` on the Flask app.
    """
    for bp in iter_blueprints():
        app.register_blueprint(bp)
