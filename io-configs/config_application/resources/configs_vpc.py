from voluptuous import Required, Schema, Optional

from config_application.data_model import ConfigVpcs
from config_application.resources.base import IOResource
from config_application.resources.validation import DefaultableResourceValidator, NonEmptyString
from config_application.utilities import make_missing_record_response


class Vpc_REST(IOResource):
    name = 'VPC'

    environment_validator = Schema({
        Required("AWS_REGION"): NonEmptyString,
        Optional("REDIS_HOST"): NonEmptyString,
        Optional("SECTION_FRONT_API_URL"): NonEmptyString,
        Optional("SETTINGS_API"): NonEmptyString,
        Optional("RESIZER_KEY"): NonEmptyString,

        Optional("SITESERVICE_API"): NonEmptyString,
        Optional("CANONICALSERVICE_API"): NonEmptyString,
        Optional("AUTHORSERVICE_API"): NonEmptyString,
        Optional("PHOTO_API"): NonEmptyString,
        Optional("STORY_API"): NonEmptyString,
        Optional("CONTENT_API"): NonEmptyString,
        Optional("CONTENT_OPS"): NonEmptyString,
    })

    validator = DefaultableResourceValidator({
        Required('vpc'): str,
        Required('environments'): Schema({
            str: environment_validator
        }, required=True),
    })

    default_db_model = ConfigVpcs

    def get(self, resource_id, env=None, **kwargs):
        ''' return a record '''
        result, status = super().get(resource_id, **kwargs)
        if env and status == 200:
            envs = result.get("environments", {}).get(env)
            if not envs:
                return make_missing_record_response("Environment")
            return envs, 200
        return (result, status)

    # TODO handle merging of environments on put/post
