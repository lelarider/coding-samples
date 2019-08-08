from flask import current_app
from config_application import data_model
from config_application.const import IS_INSTANCE_MAP, TABLE_REQS

orgs = data_model.ConfigOrgs
template = data_model.ConfigTemplate


def make_missing_record_response(field):
    return f'{field} not found', 404


# example: there are two (web_url and field_title)
# required for each client. verify that required fields have either
# already been configured for client or in newest update
def config_values_check(org_config, request_object, table):
    required_fields = TABLE_REQS[table]['required']
    issues = []
    merged = {**org_config, **request_object}
    for field in required_fields:
        if field not in merged:
            issues.append(field)
    if len(issues) > 0:
        return {'message': 'required fields: {}'.format(', '.join(issues))}


def field_requirements_check(config, table):
    field_requirements = TABLE_REQS[table]['field_types']
    issues = []
    for field in config:
        variable = config.get(field)
        field_type = field_requirements.get(field, str)
        if not isinstance(variable, field_type):
            issues.append(field)
    if len(issues) > 0:
        return {'message': 'Invalid field type for: {}'.format(', '.join(issues))}


def user_validation(key, user_role):
    template_field_roles = template.get(key).roles
    if user_role not in template_field_roles:
        return False
    else:
        return True


def type_validation(request_object):
    issues = []
    for key, value in request_object.items():
        valid = False
        try:
            template_field = template.get(key)
        except:
            return {'message': 'Invalid field name: {}'.format(key)}
        for t in template_field.type:
            if isinstance(value, IS_INSTANCE_MAP.get(t)):
                valid = True
        if valid is False:
            issues.append(key)
    if len(issues) > 0:
        return {'message': 'User role or field type issues for: {}'.format(', '.join(issues))}


def org_environs_listing(org):
    environs = orgs.get(org).environments
    environ_envs = set()
    for k, v in environs.items():
        environ_envs |= set(v)
    return environ_envs
