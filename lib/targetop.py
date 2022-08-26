import inspect


class TargetOp:
    def __init__(self, fn):
        self._fn = fn
        self._fn_params = inspect.signature(fn).parameters

    def __call__(self, pinproxy, progressbar, mem=None, **kwargs):
        kwargs.update({
            "pinproxy": pinproxy,
            "progressbar": progressbar,
            "mem": mem,
        })
        fn_kwargs = _fill_params(self._fn_params, kwargs)
        return self._fn(**fn_kwargs)

    def does_need_input(self):
        return "mem" in self._fn_params


def _fill_params(params, kwargs):
    result = {}
    for k, v in params.items():
        value = v.default if v.default != v.empty else None
        result[k] = kwargs.get(k, value)
    return result
