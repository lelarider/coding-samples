import copy
import json
import logging
import os
import redis

from flask import request, current_app
from flask_restful import Resource

from config_application import data_model
from config_application.resources.configs_org import Org_REST
from config_application.resources.configs_vpc import Vpc_REST
from config_application.utilities import config_values_check, type_validation, org_environs_listing

logger = logging.getLogger(__name__)

orgs = data_model.ConfigOrgs
config = data_model.ThisConfig
template = data_model.ThisTemplate
redis_client = redis.StrictRedis(host=os.getenv('REDIS_HOST'), port=6379, db=0)


def _get_configs(org, env=None):
    ''' parse config table

    values field can be string or a dict
    return the correct value for that partner's site
    '''
    config_dict = {}
    for item in config.query(org):
        if env and isinstance(item.values, dict):
            if item.values.get(env):
                config_dict[item.name] = item.values.get(env)
            else:
                config_dict[item.name] = item.values.get('_default')
        else:
            config_dict[item.name] = item.values
    return config_dict


class ConfigGlobals(Resource):
    ''' return globals config dict - replacement for yml config '''

    def get(self, vpc_requested, env_requested):

        if not request.args.get('token'):
            try:
                cache_config = redis_client.get(f"{vpc_requested}_{env_requested}")
                if cache_config:
                    json_config = json.loads(cache_config)
                    return json_config, 200
            except Exception:
                pass

        services, status = Vpc_REST().get(vpc_requested, env_requested)
        if status != 200:
            return services, status

        # get default configs
        common = _get_configs('_default', env_requested)

        # build config for each org in the vpc
        master_config = {}
        for org in orgs.rate_limited_scan():
            if org.vpc == vpc_requested:
                org_dict = copy.deepcopy(common)
                org_dict.update(services)
                for site in org.environments.get(env_requested, []):
                    site_config = _get_configs(org.org, site)
                    org_dict.update(site_config)
                    master_config[site] = copy.deepcopy(org_dict)

        return master_config, 200


class ConfigREST(Resource):
    ''' CRUD partner-feeds configuration variables

    values hold the configuration value.  It could be str, bool, int or dict.  If it's a dict it will have a key for each environment and/or _default.
    '''

    def __init__(self):
        if not config.exists():
            config.create_table()

    def template_config(self, common):
        template_configs = {}
        template_configs_fields = [
            'FEED_TITLE',
            'WEB_URL',
            'LANGUAGE',
            'DISPLAY_TIMEZONE',
            'EXCLUDE_SITES',
        ]
        for field in template_configs_fields:
            template_infos = template.get(field)
            template_configs[template_infos.key] = {
                'value': common.get(template_infos.key),
                'type': template_infos.type,
                'name': template_infos.name,
                'hint': template_infos.hint,
                'hidden': template_infos.hidden,
                'selections': template_infos.selections,
            }
        return template_configs

    def get_template(self, org):
        '''Combine template and values

        values are a combination of _default and the orgs
        '''

        common = _get_configs('_default')
        org_config = _get_configs(org)
        if not org_config:
            return {'message': 'Org does not exist'}, 400
        common.update(org_config)
        return self.template_config(common)

    def get(self, org, key=None):
        ''' combination of _default and org values '''
        common = _get_configs('_default')
        org_config = _get_configs(org)
        if org_config == {}:
            return {'message': 'Org does not exist'}, 400
        common.update(org_config)
        if 'template' in request.path:
            common = self.template_config(common)
        if key:
            return common.get(key, {})
        return common

    def post(self, org, key=None, request_object=None):
        ''' one or more dictonaries of key: values '''

        def run_checks(configs):
            # web_url and feed_title are the two required fields for all clients
            fields_qc = config_values_check(org_config, configs, 'this')
            if fields_qc:
                return fields_qc
            # template type must match new value type
            validate_field_type = type_validation(configs)
            if validate_field_type:
                return validate_field_type

        def process_configs(key, value, environ_envs):
            field_check = template.count(key)
            if field_check > 0:
                # check to make sure dict key is an env or "_default"
                if isinstance(value, dict):
                    for entry in value:
                        if entry not in environ_envs and entry != "_default":
                            return {'message': "Dict entries must have key of {}, or _default".format(', '.join(environ_envs))}, 400
                new_config = config(org, key)
                new_config.values = value
                new_config.save()
                return new_config.values

        def merge_and_check(value):
            current_config = org_config.get(key, {})
            if isinstance(current_config, dict):
                updated_config = {**current_config, **value}
            else:
                updated_config = value
            if current_config == updated_config:
                return True
            return updated_config

        qc_org = org
        if qc_org.startswith('sandbox.'):
            qc_org = qc_org.replace('sandbox.', '')
        junk, status = Org_REST().get(qc_org)
        if status != 200:
            return {'message': 'Org does not exist'}, 400
        if request_object is None:
            request_object = request.json

        # get current org configs and environemtns (sandbox, prod, websites) available for org
        org_config = _get_configs(qc_org)
        environ_envs = org_environs_listing(qc_org)

        if key:  # updating only one config specified in url path
            current_configs = org_config.get(key)
            merge_qc = False  # merge qc func will merge current and request values. will return True if configs match; else will return merged dict for processing
            if isinstance(request_object, dict):
                # check if key is a valid environment or _default
                if any(org in request_object for org in environ_envs) or '_default' in request_object.keys():
                    merge_qc = merge_and_check(request_object)
                    if merge_qc is True:
                        return {'message': 'Entry matches current value'}, 400
            elif current_configs == request_object:
                return {'message': 'Entry matches current value'}, 400
            validation_qc = run_checks({key: request_object})
            if validation_qc:
                return validation_qc, 400
            if merge_qc:
                return {key: process_configs(key, merge_qc, environ_envs)}
            else:
                return {key: process_configs(key, request_object, environ_envs)}

        else:  # list of configs to be updated
            status = {
                'matching entries': [],
                'successes': []
            }
            validation_qc = run_checks(request_object)
            if validation_qc:
                return validation_qc, 400
            for key, value in request_object.items():
                # check to see if valid variable name and if variable value has been updated
                if isinstance(value, dict):
                    if any(org in value for org in environ_envs) or '_default' in value.keys():
                        merge_qc = merge_and_check(value)  # merge qc will result in merged current and updated dicts if valid
                        if merge_qc is True:
                            status['matching entries'].append(f'{key} matches current {key} value')
                        else:
                            process_configs(key, merge_qc, environ_envs)
                            status['successes'].append({key: merge_qc})
                elif org_config.get(key) == value:
                    status['matching entries'].append(f'{key} matches current {key} value')
                else:
                    process_configs(key, value, environ_envs)
                    status['successes'].append({key: value})
            return status

    def put(self, org, key=None, request_object=None):
        if request_object is None:
            request_object = request.json
        return self.post(org, key, request_object)

    def delete(self, org, key=None):
        ''' Delete config

        Three valid options
        pass the key in the url
        pass json { "KEY": "VALUE" }
        pass json { "KEY": {"website": "value"}}
        '''
        junk, status = Org_REST().get(org)
        if status != 200:
            return {'message': 'Org does not exist'}, 400
        del_object = request.json
        deleted = []
        if key:
            key = key.upper()
            config(org, key).delete()
            return {'message': '{} DELETED'.format(key)}, 200
        elif isinstance(del_object, dict):
            orig_config = _get_configs(org)
            for k, v in del_object.items():
                # look for a websites config value
                if isinstance(v, dict):
                    for field in v:
                        # if match, delete just that websites key
                        # need to check for None in case it's a False value
                        if orig_config.get(k, {}).get(field) is not None:
                            del orig_config[k][field]
                            deleted.append('{}-{}'.format(k, field))
                    if not orig_config[k]:
                        # no more websites, delete the whole thing
                        # TODO if only 1 values, should it be _default
                        config(org, k).delete()
                    else:
                        # save remaining keys
                        c = config(org, k)
                        c.values = orig_config[k]
                        c.save()
                elif isinstance(v, list):
                    # ie. {"FIELDS": ["WEB_URL", "ORG"]}
                    for field in v:
                        # delete the key in the json body
                        config(org, field).delete()
                        deleted.append(field)
                else:
                    # delete the key in the json body
                    config(org, k).delete()
                    deleted.append(k)
            return {'message': '{} DELETED'.format(", ".join(deleted))}, 200
        else:
            return {'message': 'Invalid request'}, 400
