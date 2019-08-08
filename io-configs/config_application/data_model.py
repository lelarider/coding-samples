import logging
import os

from pynamodb.attributes import JSONAttribute, ListAttribute, UnicodeAttribute
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from pynamodb.models import Model

LOG = logging.getLogger(__name__)


DEFAULT_AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
DEFAULT_DB_HOST = os.environ.get('DYNAMO_HOST')

LOG.info("Using AWS_REGION %s", DEFAULT_AWS_REGION)
if DEFAULT_DB_HOST:
    LOG.info("Using DynamoDB host %s", DEFAULT_DB_HOST)


def build_meta_model(db_table_name, db_region=None, read_capacity=1, write_capacity=1, db_host=None):
    if not db_region:
        db_region = DEFAULT_AWS_REGION
    if not db_host:
        db_host = DEFAULT_DB_HOST
    class ArcIOModelMeta:
        table_name = db_table_name
        region = db_region
        read_capacity_units = read_capacity
        write_capacity_units = write_capacity
    # so testing can specify a locally hosted dynamo db
    if db_host:
        ArcIOModelMeta.host = db_host
    return ArcIOModelMeta


class BaseModel(Model):
    debug_mode = False

    def to_dict(self):
        fields = {}
        for field in self._get_attributes():
            fields[field] = getattr(self, field)
        return fields

    def from_dict(self, kwargs):
        self._set_attributes(**kwargs)

    def __repr__(self):
        return str(self.to_dict())

    def save(self):
        if self.debug_mode:
            LOG.warning("*DEBUG MODE*, NOT SAVED!")
        else:
            super(BaseModel, self).save()

    def delete(self):
        if self.debug_mode:
            LOG.warning("*DEBUG MODE*, NOT SAVED!")
        else:
            super(BaseModel, self).delete()


class BaseDefaultableModel(BaseModel):
    values = None
    org = None
    name = None

    @property
    def defaultable_field(self):
        return self.values

    @defaultable_field.setter
    def defaultable_field(self, vals):
        self.values = vals

    @property
    def hash_key(self):
        return self.org

    @property
    def range_key(self):
        return self.name

    def to_dict(self):
        return self.defaultable_field

    def from_dict(self, vals):
        self.defaultable_field = vals


class CofnigAuths(BaseModel):
    """
    Auth Table
    """
    Meta = build_meta_model('io-auths')
    username = UnicodeAttribute(hash_key=True)
    password = UnicodeAttribute(null=False)
    partner_access = ListAttribute(default=[])
    role = UnicodeAttribute(default='admin')


class ConfigOrgs(BaseModel):
    """
    Organizations Table
    """
    Meta = build_meta_model('io-orgs')
    org = UnicodeAttribute(hash_key=True)
    vpc = UnicodeAttribute()
    environments = JSONAttribute()
    websites = JSONAttribute()


class ConfigVpcs(BaseModel):
    """
    VPC Table
    """
    Meta = build_meta_model('io-vpcs')
    vpc = UnicodeAttribute(hash_key=True)
    environments = JSONAttribute()


class GlobalConfig(BaseModel):
    """
    global configurations
    """
    Meta = build_meta_model('global_config', None, 5, 1)
    org = UnicodeAttribute(hash_key=True)
    name = UnicodeAttribute(range_key=True)
    values = JSONAttribute()


class GlobalTemplate(BaseModel):
    """
    global configuration field definitions
    """
    Meta = build_meta_model('global_template', None, 5, 1)
    key = UnicodeAttribute(hash_key=True)
    name = UnicodeAttribute(null=True)
    hint = UnicodeAttribute(null=True)
    hidden = UnicodeAttribute(default=True)
    roles = JSONAttribute(default=['admin'])
    type = JSONAttribute()
    selections = JSONAttribute(null=True)
