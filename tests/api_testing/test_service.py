# from eva.utils.time_ import utc_rfc3339_string

import os
import uuid

from codebase.models import Service
from codebase.utils.swaggerui import api
from codebase.utils.fetch_with_form import post
from eva.utils.time_ import utc_rfc3339_string

from .base import (
    BaseTestCase,
    validate_default_error,
    get_body_json
)


class _Base(BaseTestCase):

    rs = api.spec.resources["service"]


class ServiceListTestCase(_Base):
    """GET /service - 查看所有服务列表
    """

    def test_list_success(self):
        """正确
        """
        total = 5
        basename = "fortest"
        for i in range(total):
            srv = Service(name=basename+str(i))
            self.db.add(srv)
        self.db.commit()

        resp = self.api_get("/service")
        body = get_body_json(resp)
        self.assertEqual(resp.code, 200)
        self.validate_default_success(body)

        spec = self.rs.get_service.op_spec["responses"]["200"]["schema"]
        api.validate_object(spec, body)

        self.assertEqual(len(body["data"]), total)


class ServiceCreateTestCase(_Base):
    """POST /service - 创建服务
    """

    def test_name_exist(self):
        """使用重复的名称
        """

        name = "fortest"
        srv = Service(name=name)
        self.db.add(srv)
        self.db.commit()

        resp = post(self.fetch, "/service", files={}, params={"name": name})
        body = get_body_json(resp)
        self.assertEqual(resp.code, 400)
        validate_default_error(body)
        self.assertEqual(body["status"], "name-exist")

    def test_create_success(self):
        """创建成功
        """
        curdir = os.path.dirname(__file__)
        spec_path = os.path.join(curdir, "../../src/codebase/schema.yml")
        name = "fortest"
        resp = post(self.fetch, "/service", files={
            "openapi": spec_path}, params={"name": name})
        body = get_body_json(resp)
        self.assertEqual(resp.code, 200)
        self.validate_default_success(body)

        srv = self.db.query(Service).filter_by(name=name).first()
        self.assertIsNot(srv, None)
        self.assertEqual(str(srv.uuid), body["id"])


class SingleServiceViewTestCase(_Base):
    """GET /service/{id} - 查看指定的服务详情
    """

    def test_not_found(self):
        """ID不存在
        """

        srv_id = str(uuid.uuid4())
        resp = self.api_get(f"/service/{srv_id}")
        self.validate_not_found(resp)

    def test_get_success(self):
        """正确
        """
        name = "name"
        summary = "summary"
        srv = Service(name=name, summary=summary)
        self.db.add(srv)
        self.db.commit()

        resp = self.api_get(f"/service/{srv.uuid}")
        body = get_body_json(resp)
        self.assertEqual(resp.code, 200)
        self.validate_default_success(body)

        spec = self.rs.get_service_id.op_spec["responses"]["200"]["schema"]
        api.validate_object(spec, body)

        data = body["data"]
        self.assertEqual(data["summary"], summary)
        self.assertEqual(data["created"], utc_rfc3339_string(srv.created))
        self.assertEqual(data["updated"], utc_rfc3339_string(srv.updated))


class ServiceUpdateTestCase(_Base):
    """POST /service/{id} - 更新服务属性
    """

    def test_not_found(self):
        """ID不存在
        """
        srv_id = str(uuid.uuid4())
        resp = self.api_post(f"/service/{srv_id}")
        self.validate_not_found(resp)

    def test_name_exist(self):
        """服务名已存在
        """

        exist_name = "exist_name"
        srv = Service(name=exist_name)
        self.db.add(srv)
        self.db.commit()

        srv = Service(name="name")
        self.db.add(srv)
        self.db.commit()

        resp = self.api_post(f"/service/{srv.uuid}", body={"name": exist_name})
        body = get_body_json(resp)
        self.assertEqual(resp.code, 400)
        validate_default_error(body)

        self.assertEqual(body["status"], "name-exist")

    def test_update_success(self):
        """更新成功
        """

        name = "name"
        summary = "summary"
        description = "description"

        srv = Service(name=name, summary=summary, description=description)
        self.db.add(srv)
        self.db.commit()
        old_updated = srv.updated
        srv_id = str(srv.uuid)
        del srv

        resp = self.api_post(f"/service/{srv_id}", body={
            "name": name + ":new",
            "summary": summary + ":new",
            "description": description + ":new"})
        body = get_body_json(resp)
        self.assertEqual(resp.code, 200)
        self.validate_default_success(body)

        srv = self.db.query(Service).filter_by(uuid=srv_id).one()
        self.assertEqual(srv.summary, summary + ":new")
        self.assertEqual(srv.description, description + ":new")
        self.assertNotEqual(old_updated, srv.updated)


# class RoleDeleteTestCase(RoleBaseTestCase):
#     """DELETE /role/{id} - 删除角色
#     """
#
#     def test_not_found(self):
#         """角色ID不存在
#         """
#         role_id = str(uuid.uuid4())
#         resp = self.api_delete(f"/role/{role_id}")
#         self.validate_not_found(resp)
#
#     def test_delete_success(self):
#         """删除成功
#         """
#         user_id = self.current_user.id
#
#         role_name = "my-role"
#         role = Role(name=role_name)
#         role.users.append(self.current_user)
#         perm = Permission(name="my-permission")
#         self.db.add(perm)
#         role.permissions.append(perm)
#         self.db.add(role)
#         self.db.commit()
#
#         role_id = str(role.uuid)
#         resp = self.api_delete(f"/role/{role_id}")
#         body = get_body_json(resp)
#         self.assertEqual(resp.code, 200)
#         self.validate_default_success(body)
#
#         dbc.remove()
#
#         role = self.db.query(Role).filter_by(uuid=role_id).first()
#         self.assertIs(role, None)
#
#         user = self.db.query(User).get(user_id)
#         self.assertNotIn(role_name, [r.name for r in user.roles])
