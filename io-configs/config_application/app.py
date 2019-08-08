from jmespath import search as jq
import logging
import sys

from flask import Flask, Response, request, current_app
from flask_restful import Api

from config_application.data_model import ConfigAuths, BaseModel
from config_application.resources.configs_org import Org_REST
from config_application.resources.configs_vpc import Vpc_REST
from config_application.resources.configs import ConfigGlobals, ConfigREST


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s: %(name)s: %(levelname)s: %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)


def get_app(api_key, secret_key=None, read_only_mode=False):
    if not secret_key:
        secret_key = `SECRET_KEY_HERE`

    app = Flask(__name__)
    app.secret_key = secret_key
    app.config['API_KEY'] = api_key

    if read_only_mode:
        print("*READ ONLY MODE*, NOTHING WILL BE SAVED!")
        BaseModel.debug_mode = True

    get_api(app)

    def check_auth(request):
        # if accessing special mode, only the "/special_path" special_file.py file is accessible
        auth = request.authorization
        org = request.headers.get('Org-Name')
        if auth and org and request.full_path.startswith('/special_path'):
            auth_db = Auths()
            username = auth.username
            authorized_info = auth_db.get(username)
            authorized_password = authorized_info.password
            authorized_partners = authorized_info.partner_access
            if authorized_password == auth.password and org in authorized_partners:
                app.config['USER_ROLE'] = authorized_info.role
                return True
        else:
            logger.error("Unable to authenticate")
            return False

    @app.before_request
    def requires_auth():
        """Check for basic auth & org or for API key"""
        cookies = request.headers.get('Cookie')
        if cookies:
            for cookie in cookies.split('; '):
                print(cookie)
        if not check_auth(request):
            request_api_key = request.args.get('api_key') or request.headers.get('api_key')
            if request_api_key != current_app.config.get("API_KEY"):
                return authenticate()

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Org-Name,Site')
        response.headers.add('Access-Control-Allow-Methods', 'OPTIONS,GET,PUT,POST,DELETE')
        return response

    app.logger.addHandler(logging.StreamHandler(sys.stdout))

    return app


def get_api(flask_app):
    api = Api(flask_app)

    # Public Routes
    api.add_resource(Vpc_REST,
                     '/vpc/config/<string:resource_id>/',
                     '/vpc/config/<string:resource_id>/<string:env>/')
    api.add_resource(Org_REST, '/org/config/<string:resource_id>/')
    api.add_resource(ConfigGlobals,
                     '/configuration/globals/<string:vpc_requested>/<string:env_requested>/')
    api.add_resource(ConfigREST,
                     '/configuration/config/<string:org>/',
                     '/configuration/config/<string:org>/<string:key>/',
                     '/configuration/config/<string:org>/template/')

    return api


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Please verify ORG credentials or api key.', 401,
        {'WWW-Authenticate': 'Basic realm="Org credentials or api key required"'})
