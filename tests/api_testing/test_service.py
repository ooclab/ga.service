# from eva.utils.time_ import utc_rfc3339_string

import os

from codebase.models import Service
from codebase.utils.swaggerui import api
from codebase.utils.fetch_with_form import post

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
#
#
# class SingleRoleViewTestCase(RoleBaseTestCase):
#     """GET /role/{id} - 查看指定的角色详情
#     """
#
#     def test_not_found(self):
#         """角色ID不存在
#         """
#
#         role_id = str(uuid.uuid4())
#         resp = self.api_get(f"/role/{role_id}")
#         self.validate_not_found(resp)
#
#     def test_get_success(self):
#         """正确
#         """
#         role_name = "my-role"
#         role_summary = "my summary"
#         role = Role(name=role_name, summary=role_summary)
#         self.db.add(role)
#         self.db.commit()
#
#         resp = self.api_get(f"/role/{role.uuid}")
#         body = get_body_json(resp)
#         self.assertEqual(resp.code, 200)
#         self.validate_default_success(body)
#
#         spec = self.rs.get_role_id.op_spec["responses"]["200"]["schema"]
#         api.validate_object(spec, body)
#
#         data = body["data"]
#         self.assertEqual(data["summary"], role_summary)
#         self.assertEqual(data["created"], utc_rfc3339_string(role.created))
#         self.assertEqual(data["updated"], utc_rfc3339_string(role.updated))
#
#
# class RoleUpdateTestCase(RoleBaseTestCase):
#     """POST /role/{id} - 更新角色属性
#     """
#
#     def test_not_found(self):
#         """角色ID不存在
#         """
#         role_id = str(uuid.uuid4())
#         resp = self.api_post(f"/role/{role_id}")
#         self.validate_not_found(resp)
#
#     def test_update_success(self):
#         """更新成功
#         """
#
#         name = "my-role"
#         summary = "my summary"
#         description = "my description"
#
#         role = Role(name=name, summary=summary, description=description)
#         self.db.add(role)
#         self.db.commit()
#         old_updated = role.updated
#         role_id = str(role.uuid)
#         del role
#
#         resp = self.api_post(f"/role/{role_id}", body={
#             "summary": summary + ":new",
#             "description": description + ":new"})
#         body = get_body_json(resp)
#         self.assertEqual(resp.code, 200)
#         self.validate_default_success(body)
#
#         role = self.db.query(Role).filter_by(uuid=role_id).one()
#         self.assertEqual(role.summary, summary + ":new")
#         self.assertEqual(role.description, description + ":new")
#         self.assertNotEqual(old_updated, role.updated)
#
#
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
