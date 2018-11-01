import uuid
import mimetypes
from functools import partial

from tornado.web import HTTPError


def body_producer(boundary, files, params, write):
    if not isinstance(files, dict):
        raise HTTPError("files must be dict")
    if not isinstance(params, dict):
        raise HTTPError("params must be dict")

    boundary_bytes = boundary.encode()

    for argname in files:
        filename = files[argname]
        filename_bytes = filename.encode()
        write(b'--%s\r\n' % (boundary_bytes,))
        write(b'Content-Disposition: form-data; name="%s"; filename="%s"\r\n' %
              (argname.encode(), filename_bytes))

        mtype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        write(b'Content-Type: %s\r\n' % (mtype.encode(),))
        write(b'\r\n')
        with open(filename, 'rb') as f:
            while True:
                # 16k at a time.
                chunk = f.read(16 * 1024)
                if not chunk:
                    break
                write(chunk)

        write(b'\r\n')

    for argname in params:
        value = params[argname]
        write(b'--%s\r\n' % (boundary_bytes,))
        write(b'Content-Disposition: form-data; name="%s"\r\n\r\n%s\r\n' %
              (argname.encode(), value.encode()))

    write(b'--%s--\r\n' % (boundary_bytes,))


def post(fetch, url, files, params):
    boundary = uuid.uuid4().hex
    headers = {'Content-Type': 'multipart/form-data; boundary=%s' % boundary}
    producer = partial(body_producer, boundary, files, params)
    response = fetch(url,
                     method='POST',
                     headers=headers,
                     body_producer=producer)

    return response
