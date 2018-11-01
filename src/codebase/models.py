# pylint: disable=R0902,E1101,W0201,too-few-public-methods,W0613

import datetime
import uuid

from sqlalchemy_utils import UUIDType
from eva.utils.time_ import utc_rfc3339_string
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    Sequence,
    String,
    Text,
)

from codebase.utils.sqlalchemy import ORMBase


class Service(ORMBase):

    __tablename__ = "service_service"

    id = Column(Integer, Sequence("service_service_id_seq"), primary_key=True)
    uuid = Column(UUIDType(), default=uuid.uuid4, unique=True)
    name = Column(String(128), unique=True)
    summary = Column(String(1024))
    description = Column(Text)

    # 服务版本
    version = Column(String(16))

    # 服务状态
    status = Column(String(64))

    updated = Column(DateTime(), default=datetime.datetime.utcnow)
    created = Column(DateTime(), default=datetime.datetime.utcnow)

    @property
    def isimple(self):
        return {
            "id": str(self.uuid),
            "name": self.name,
            "status": self.status,
            "version": self.version,
            "summary": self.summary,
            "updated": utc_rfc3339_string(self.updated),
        }

    @property
    def ifull(self):
        return {
            "id": str(self.uuid),
            "name": self.name,
            "status": self.status,
            "version": self.version,
            "summary": self.summary,
            "description": self.description,
            "updated": utc_rfc3339_string(self.updated),
            "created": utc_rfc3339_string(self.created),
        }
