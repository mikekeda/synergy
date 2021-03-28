from urllib.parse import urlencode

from sanic.request import Request


def update_param(request: Request, param: str, value: str = None) -> str:
    path = request.path
    params = dict(request.query_args)
    if value:
        params[param] = value
    else:
        params.pop(param, None)

    if params:
        path += "?" + urlencode(params)

    return path
