import os
from config_application.app import get_app

read_only_mode = os.getenv('READ_ONLY_MODE')
api_key = os.environ.get('API_KEY')

if not api_key:
    raise Exception('Please specify an API key.')

app = get_app(api_key, None, read_only_mode)

if __name__ == "__main__":
    flask_env = os.getenv('FLASK_ENV')
    if flask_env == 'prod':
        app.run()
    else:
        # the host is so docker can connect to this port
        app.run(host='0.0.0.0', port=5000, debug=True)
