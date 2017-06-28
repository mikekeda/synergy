from urllib.parse import urlencode


def update_param(request, param, value=None):
    path = request.path
    params = request.raw_args
    if value:
        params[param] = value
    else:
        params.pop(param, None)

    if params:
        path += '?' + urlencode(params)

    return path
