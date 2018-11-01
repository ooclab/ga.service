from tornado.web import url

from codebase.controllers import (
    default,
    service
)


HANDLERS = [
    url(r"/_spec",
        default.SpecHandler),

    url(r"/_health",
        default.HealthHandler),

    # Service

    url(r"/service",
        service.ServiceHandler),

    url(r"/service/"
        r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
        service.SingleServiceHandler),

    url(r"/service/"
        r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
        r"/openapi",
        service.UpdateOpenAPIHandler),
]
