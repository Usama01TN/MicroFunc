# coding=utf-8
"""
None
"""
from functools import partial

try:
    from functools import partialmethod
except:
    # Descriptor version
    class partialmethod(object):
        """
        Method descriptor with partial application of the given arguments
        and keywords.

        Supports wrapping existing descriptors and handles non-descriptor
        callables as instance methods.
        """

        def __init__(self, func, *args, **keywords):
            if not callable(func) and not hasattr(func, "__get__"):
                raise TypeError("{!r} is not callable or a descriptor"
                                .format(func))

            # func could be a descriptor like classmethod which isn't callable,
            # so we can't inherit from partial (it verifies func is callable)
            if isinstance(func, partialmethod):
                # flattening is mandatory in order to place cls/self before all
                # other arguments
                # it's also more efficient since only one function will be called
                self.func = func.func
                self.args = func.args + args
                self.keywords = func.keywords.copy()
                self.keywords.update(keywords)
            else:
                self.func = func
                self.args = args
                self.keywords = keywords

        def __repr__(self):
            args = ", ".join(map(repr, self.args))
            keywords = ", ".join("{}={!r}".format(k, v) for k, v in (self.keywords.iteritems() if hasattr(
                self.keywords, 'iteritems') else self.keywords.items()))
            format_string = "{module}.{cls}({func}, {args}, {keywords})"
            return format_string.format(module=self.__class__.__module__,
                                        cls=self.__class__.__name__,
                                        func=self.func,
                                        args=args,
                                        keywords=keywords)

        def _make_unbound_method(self):
            def _method(*args, **keywords):
                call_keywords = self.keywords.copy()
                call_keywords.update(keywords)
                cls_or_self, rest = args[0], args[1:]
                call_args = (cls_or_self,) + self.args + tuple(rest)
                return self.func(*call_args, **call_keywords)

            _method.__isabstractmethod__ = self.__isabstractmethod__
            _method._partialmethod = self
            return _method

        def __get__(self, obj, cls):
            get = getattr(self.func, "__get__", None)
            result = None
            if get is not None:
                new_func = get(obj, cls)
                if new_func is not self.func:
                    result = partial(new_func, *self.args, **self.keywords)
                    try:
                        result.__self__ = new_func.__self__
                    except AttributeError:
                        pass
                if result is None:
                    result = self._make_unbound_method().__get__(obj, cls)
            return result

        @property
        def __isabstractmethod__(self):
            return getattr(self.func, "__isabstractmethod__", False)
