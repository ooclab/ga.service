# pylint: disable=W0223,W0221,broad-except,R0914

from sqlalchemy import and_
from tornado.web import HTTPError
from yaml import safe_load
from swagger_spec_validator.util import get_validator
from bravado_core.spec import Spec
from etcd3 import Client
from eva.conf import settings

from codebase.web import APIRequestHandler
from codebase.models import Service


def get_openapi_spec_key(service_name):
    return f"/ga/service/{service_name}/openapi/spec"


class ServiceHandler(APIRequestHandler):

    def get(self):
        """获取所有服务列表
        """
        services = self.db.query(Service).all()
        self.success(data=[srv.isimple for srv in services])

    def post(self):
        """创建服务
        """

        name = self.get_argument("name")
        srv = self.db.query(Service).filter_by(name=name).first()
        if srv:
            self.fail("name-exist")
            return

        version = ""
        summary = ""
        description = ""

        # 处理 openapi
        file_metas = self.request.files["openapi"]
        for meta in file_metas:
            data = meta["body"]

            # 1. validate spec
            spec_json = safe_load(data)
            validator = get_validator(spec_json)
            validator.validate_spec(spec_json)

            # 2. get summary from spec
            spec = Spec.from_dict(spec_json)
            version = spec.spec_dict["info"]["version"]
            summary = spec.spec_dict["info"]["title"]
            description = spec.spec_dict["info"]["description"]
            if not summary:
                print(description.split("\n"))
                summary = description.split("\n")[0]

            # 3. upload file to etcd
            for endpoint in settings.ETCD_ENDPOINTS.split(";"):
                host, port = endpoint.split(":")
                client = Client(host, int(port))
                key = get_openapi_spec_key(name)
                client.put(key, data)
                break  # FIXME: try when failed

        srv = Service(
            name=name,
            version=version,
            summary=summary,
            description=description)
        self.db.add(srv)
        self.db.commit()
        self.success(id=str(srv.uuid))


class _BaseSingleServiceHandler(APIRequestHandler):

    def get_service(self, _id):
        srv = self.db.query(Service).filter_by(uuid=_id).first()
        if srv:
            return srv
        raise HTTPError(400, reason="not-found")


class SingleServiceHandler(_BaseSingleServiceHandler):

    def get(self, _id):
        """获取服务详情
        """
        srv = self.get_service(_id)
        self.success(data=srv.ifull)

    def post(self, _id):
        """更新服务属性

        TODO: 除了名称，其他还是以服务的 OpenAPI Spec 为准？
        """
        srv = self.get_service(_id)
        body = self.get_body_json()
        if "name" in body:
            name = body.pop("name")
            if self.db.query(Service).filter(and_(
                    Service.name == name, Service.id != srv.id)).first():
                self.fail("name-exist")
                return
            srv.name = name
        if "summary" in body:
            srv.summary = body.pop("summary")
        if "description" in body:
            srv.description = body.pop("description")
        self.db.commit()
        self.success()

    def delete(self, _id):
        """删除服务
        """
        srv = self.get_service(_id)
        self.db.delete(srv)
        self.db.commit()

        # 3. upload file to etcd
        for endpoint in settings.ETCD_ENDPOINTS.split(";"):
            host, port = endpoint.split(":")
            client = Client(host, int(port))
            key = get_openapi_spec_key(srv.name)
            client.delete_range(key)
            break  # FIXME: try when failed

        self.success()
