# -*- coding: utf-8 -*-
"""
lazy_import - deferred imports that work on Python 2.6/2.7 *and* Python 3.
Python 3 has ``importlib.util.LazyLoader`` (3.5+) and module-level
``__getattr__`` (PEP 562, 3.7+). Python 2 has neither, so this module
re-implements both ideas using only things Python 2 supports:
1. ``lazy_import(name)`` - returns a module proxy. The real import runs the
   first time any attribute is touched; after that the proxy rebinds the
   caller's global name to the real module, so later access costs nothing.
       np = lazy_import('numpy')        # nothing imported yet
       def f(x):
           return np.array(x)           # numpy imported here, once
2. ``lazy_module_attrs(__name__, {...})`` - a PEP 562 backport for packages.
   Lets ``pkg.heavy`` / ``from pkg import Thing`` resolve on first use.
       # pkg/__init__.py
       from lazy_import import lazy_module_attrs
       lazy_module_attrs(__name__, {
           'heavy': '.heavy',                    # submodule
           'Thing': ('.things', 'Thing'),        # object inside a module
       })
Both are thread-safe. Import errors surface at first use, not at the
``lazy_import`` line - that is the trade-off of any lazy import.
"""
from __future__ import absolute_import
from sys import modules, _getframe
from types import ModuleType
from threading import RLock

try:
    from importlib import import_module as _import_module   # 2.7+, 3.x
except:                                          # pragma: no cover
    def _import_module(name, package=None):                  # 2.6 fallback
        if name.startswith('.'):
            if not package:
                raise TypeError("relative import requires 'package'")
            level = len(name) - len(name.lstrip('.'))
            base = package.rsplit('.', level - 1)[0]
            name = base + '.' + name[level:] if name[level:] else base
        __import__(name)
        return modules[name]

__all__ = ['lazy_import', 'lazy_module_attrs', 'LazyModule', 'is_loaded']
# Attributes that live on the proxy itself and never trigger the import.
_PROXY_ATTRS = frozenset([
    '__class__', '__dict__', '_lazy_load', '_lazy_name', '_lazy_package', '_lazy_module', '_lazy_lock', '_lazy_globals'
])


class LazyModule(ModuleType):
    """
    Stand-in for a module that imports the real one on first use.
    """

    def __init__(self, name, package=None, caller_globals=None):
        ModuleType.__init__(self, name)
        d = object.__getattribute__(self, '__dict__')
        d['_lazy_name'] = name
        d['_lazy_package'] = package
        d['_lazy_module'] = None
        d['_lazy_lock'] = RLock()
        d['_lazy_globals'] = caller_globals

    def _lazy_load(self):
        d = object.__getattribute__(self, '__dict__')
        mod = d['_lazy_module']
        if mod is not None:
            return mod
        with d['_lazy_lock']:
            mod = d['_lazy_module']
            if mod is None:
                mod = _import_module(d['_lazy_name'], d['_lazy_package'])
                d['_lazy_module'] = mod
                # Swap the proxy for the real module in the caller's
                # namespace so future lookups skip the proxy entirely.
                g = d['_lazy_globals']
                if g is not None:
                    for key, value in list(g.items()):
                        if value is self:
                            g[key] = mod
                    d['_lazy_globals'] = None
        return mod

    def __getattribute__(self, attr):
        if attr in _PROXY_ATTRS:
            return object.__getattribute__(self, attr)
        load = object.__getattribute__(self, '_lazy_load')
        return getattr(load(), attr)

    def __setattr__(self, attr, value):
        setattr(object.__getattribute__(self, '_lazy_load')(), attr, value)

    def __delattr__(self, attr):
        delattr(object.__getattribute__(self, '_lazy_load')(), attr)

    def __dir__(self):
        return dir(object.__getattribute__(self, '_lazy_load')())

    def __repr__(self):
        d = object.__getattribute__(self, '__dict__')
        if d['_lazy_module'] is not None:
            return repr(d['_lazy_module'])
        return '<lazy module %r (not yet imported)>' % (d['_lazy_name'],)


def lazy_import(name, package=None):
    """
    Return a lazily-imported module.
    If the module is already in ``sys.modules`` it is returned directly,
    since there is nothing to defer. ``lazy_import('a.b')`` returns the
    submodule ``a.b`` (like ``importlib.import_module``), not package ``a``.
    For relative names pass ``package=__name__`` (or ``__package__``).
    """
    if not name.startswith('.') and name in sys.modules:
        return modules[name]
    try:
        caller_globals = _getframe(1).f_globals
    except (AttributeError, ValueError):     # non-CPython without _getframe
        caller_globals = None
    return LazyModule(name, package, caller_globals)


def is_loaded(obj):
    """
    True if ``obj`` is a real module or a proxy that has been imported.
    """
    if isinstance(obj, LazyModule):
        return object.__getattribute__(obj, '__dict__')['_lazy_module'] is not None
    return isinstance(obj, ModuleType)


def lazy_module_attrs(module_name, mapping):
    """
    Give module ``module_name`` lazily-resolved attributes (PEP 562 backport).
    ``mapping`` values are either a module name (``'pkg.sub'`` or ``'.sub'``)
    or a ``(module_name, attribute_name)`` tuple. Call it from the module
    itself: ``lazy_module_attrs(__name__, {...})``.
    Note: as with PEP 562, a *bare* global name inside the module itself
    (``heavy.run()`` in a function body) is not routed through this hook
    until something has accessed ``pkg.heavy`` once; after that the value is
    cached into the module's globals and bare names work too.
    """
    original = sys.modules[module_name]
    package = original.__dict__.get('__package__') or (
        module_name if hasattr(original, '__path__') else module_name.rpartition('.')[0])
    lock = RLock()
    targets = dict(mapping)
    class _LazyAttrModule(ModuleType):
        # Keep the original module alive: on Python 2, a module being freed
        # sets all its globals to None, breaking every function defined in it.
        _lazy_original = original
        def __getattr__(self, attr):       # only called when attr is missing
            try:
                target = targets[attr]
            except KeyError:
                raise AttributeError('module %r has no attribute %r' % (module_name, attr))
            with lock:
                cached = self.__dict__.get(attr, _MISSING)
                if cached is not _MISSING:
                    return cached
                if isinstance(target, tuple):
                    mod_name, obj_name = target
                    value = getattr(_import_module(mod_name, package), obj_name)
                else:
                    value = _import_module(target, package)
                self.__dict__[attr] = value         # fast path next time
                original.__dict__[attr] = value     # visible to module's own code
            return value

        def __dir__(self):
            return sorted(set(self.__dict__) | set(targets))

    new = _LazyAttrModule(module_name, original.__doc__)
    new.__dict__.update(original.__dict__)
    sys.modules[module_name] = new
    return new


_MISSING = object()

# if __name__ == '__main__':
#     # 1. Lazy module (like `import numpy`, but deferred).
#     from lazy_import import lazy_import
#     np = lazy_import('numpy')          # Nothing imported yet
#     np.array([1, 2])                   # numpy imports here, once
#     # 2. Lazy attributes on a package (Python 2 version of Python 3's module __getattr__)
#     # pkg/__init__.py
#     from lazy_import import lazy_module_attrs
#     lazy_module_attrs(__name__, {
#         'heavy': '.heavy',               # pkg.heavy imported on first use
#         'Thing': ('.things', 'Thing'),   # `from pkg import Thing` imported on first use.
#     })
