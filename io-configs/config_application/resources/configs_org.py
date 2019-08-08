from voluptuous import Optional, Required, Schema

from config_application.resources.base import IOResource
from config_application.resources.validation import SimpleResourceValidator
from config_application.data_model import ConfigOrgs


class Org_REST(IOResource):
    validator = SimpleResourceValidator({
        Required('org'): str,
        Required('vpc'): str,
        Required('environments'): Schema({
            str: list
        }, required=True),
        Optional('websites'): dict
    })
    default_db_model = ConfigOrgs
