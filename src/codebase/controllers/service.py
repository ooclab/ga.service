# pylint: disable=W0223,W0221,broad-except,C0103,R0201,R0914

import datetime
import json
import logging

from sqlalchemy import and_
from tornado.web import HTTPError
from tornado.httpclient import AsyncHTTPClient
from yaml import safe_load
from swagger_spec_validator.util import get_validator
from bravado_core.spec import Spec
from etcd3 import Client
from eva.conf import settings

from codebase.web import APIRequestHandler
from codebase.models import Service


def get_openapi_spec_key(service_name):
    return f"/ga/service/{service_name}/openapi/spec"


def save_openapi(name, data):

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
        summary = description.split("\n")[0]

    # 3. upload file to etcd
    for endpoint in settings.ETCD_ENDPOINTS.split(";"):
        host, port = endpoint.split(":")
        client = Client(host, int(port))
        key = get_openapi_spec_key(name)
        client.put(key, data)
        break  # FIXME: try when failed

    return {
        "version": version,
        "summary": summary,
        "description": description,
    }


def get_perm_roles(service_name, data):
    spec_json = safe_load(data)
    spec = Spec.from_dict(spec_json)

    perm_roles = []

    for key in spec.resources:
        rs = spec.resources[key]
        for attr in dir(rs):
            if attr.startswith("__"):
                continue

            op = getattr(rs, attr)

            # get roles
            roles = op.op_spec.get("x-roles", [])
            if "Authorization" in op.params:
                if "authenticated" not in roles:
                    roles.append("authenticated")
            else:
                if "anonymous" not in roles:
                    roles.append("anonymous")

            # get permission name
            perm = ":".join([service_name, op.http_method, op.path_name])

            # save
            perm_roles.append((perm, roles))

    return perm_roles


class ServiceHandler(APIRequestHandler):

    def get(self):
        """获取所有服务列表
        """
        services = self.db.query(Service).all()
        self.success(data=[srv.isimple for srv in services])

    async def post(self):
        """创建服务
        """

        name = self.get_argument("name")
        srv = self.db.query(Service).filter_by(name=name).first()
        if not srv:
            srv = Service(name=name)
            self.db.add(srv)

        spec_info = {}
        errors = []

        # 处理 openapi
        file_metas = self.request.files["openapi"]
        for meta in file_metas:
            data = meta["body"]
            spec_info = save_openapi(name, data)

            # update to service
            http_client = AsyncHTTPClient()
            for perm, roles in get_perm_roles(name, data):
                for role in roles:
                    url = self.get_full_url(f"/authz/role/permission/append")
                    body = json.dumps({"role": role, "permissions": [perm]})
                    resp = await http_client.fetch(
                        url, method="POST", body=body, raise_error=False)
                    respBody = json.loads(resp.body)
                    status = respBody["status"]
                    if status != "success":
                        logging.error(
                            "update role permissions failed. resp.body = %s",
                            resp.body)
                        errors.append({"name": perm, "error": status})

        if errors:
            self.fail(errors=errors)
            return

        srv.version = spec_info.get("version")
        srv.summary = spec_info.get("summary")
        srv.description = spec_info.get("description")
        self.db.commit()
        self.success(id=str(srv.uuid))

    def get_full_url(self, url):
        return settings.INTERNAL_APIGATEWAY + url


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
        arg_len = len(body)
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
        if arg_len != len(body):
            srv.updated = datetime.datetime.utcnow()
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


class UpdateOpenAPIHandler(_BaseSingleServiceHandler):

    def post(self, _id):
        """更新OpenAPI
        """
        srv = self.get_service(_id)
        spec_info = {}

        # 处理 openapi
        file_metas = self.request.files["openapi"]
        for meta in file_metas:
            data = meta["body"]
            spec_info = save_openapi(srv.name, data)
            srv.version = spec_info.get("version")
            srv.summary = spec_info.get("summary")
            srv.description = spec_info.get("description")
            srv.updated = datetime.datetime.utcnow()
            self.db.commit()

        self.success()
