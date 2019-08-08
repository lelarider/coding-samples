import json
import logging

from flask import request
from flask_restful import Resource

from config_application import data_model
from config_application.utilities import field_requirements_check
from config_application.const import TABLE_REQS

logger = logging.getLogger(__name__)

template = data_model.Partner_feeds_template
field_types = TABLE_REQS['template']['field_types']


class Template_REST(Resource):

    def __init__(self):
        if not template.exists():
            template.create_table()

    ''' CRUD partner-feeds template API '''
    def get(self, key=None):
        if key:
            key = key.upper()
            return template.get(key).attribute_values
        else:
            return json.loads(template.dumps())

    def post(self, key=None):
        def table_update(key, entry):
            o = template(key)
            o.name = entry.get('name', '')
            o.hint = entry.get('hint', '')
            o.hidden = entry.get('hidden', '')
            o.roles = entry.get('roles', [])
            o.type = entry['type']
            o.save()
            return entry

        def new_key(key, fields):
            key = key.upper()
            field_check = template.count(key)
            if field_check > 0:  # update field
                current = template.get(key).attribute_values
                if fields.items() <= current.items():
                    return {'message': 'Templates match'}, 400
                else:
                    for k, v in fields.items():
                        key_type = field_types.get(k, str)
                        if not isinstance(v, key_type):
                            return {'message': 'field {} invalid type'.format(k)}, 400
                        try:
                            if fields[k] != current[k]:  # if field type is ok
                                #  and values are different
                                current[k] = v
                        except Exception:
                            return {'message': 'Error processing {} field'.format(k)}, 400
                    return table_update(key, current)
            else:  # new field
                return table_update(key, fields)
            return {'message': 'Invalid request'}, 400

        template_obj = request.json
        if key:
            return new_key(key, template_obj)

        else:
            returns = []
            for obj in template_obj:
                for o in template_obj[obj]:
                    fields_qc = field_requirements_check(template_obj[obj][o], 'template')
                    if fields_qc:
                        return fields_qc
                    else:
                        returns.append(new_key(o, template_obj[obj][o]))
            return returns

    def put(self):
        return self.post()

    def delete(self, key=None):
        template_obj = request.json
        try:
            if key:
                key = key.upper()
                template(key).delete()
                return {'message': '{} DELETED'.format(key)}, 200
            else:
                deleted = []
                for obj in template_obj:
                    key = obj.upper()
                    template(key).delete()
                    deleted.append(key)
                return {'message': '{} DELETED'.format(", ".join(deleted))}, 200
        except Exception:
            return {'message': 'Invalid request'}, 400
