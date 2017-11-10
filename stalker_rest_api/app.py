import json
import pathlib

import stalker
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_restful import Api
from resources.auth import Login
from resources.user import User, UserList

app = Flask(__name__)
app.secret_key = 'secretkey'  # FIXME: just for testing
api = Api(app, prefix='/api')
jwt = JWTManager(app)
api.add_resource(Login, '/login')
api.add_resource(User, '/user/<string:login>')
api.add_resource(UserList, '/users')


def connect_to_stalker():
    """Setup the connection to the Stalker database"""
    root = pathlib.Path(__file__).parent
    stalker_config_filepath = root / ".stalker_config.json"
    with stalker_config_filepath.open("r") as stalker_config_file:
        stalker_config = json.load(stalker_config_file)
    database_engine_settings = stalker_config.get("database_engine_settings")
    stalker.db.setup(settings=database_engine_settings)


def main():
    connect_to_stalker()
    app.run(port=5000, debug=True)


if __name__ == "__main__":
    main()
