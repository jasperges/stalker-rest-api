import pathlib
import json

from flask import Flask, request
from flask_restful import Resource, Api
from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    create_access_token,
    get_jwt_identity,
)
from marshmallow import Schema, fields, post_load
from sqlalchemy import or_

from stalker import db, User, Project
from stalker.db.session import DBSession

app = Flask(__name__)
app.secret_key = 'secretkey'  # FIXME: just for testing
api = Api(app)
jwt = JWTManager(app)


# Connect to Stalker (test) database
def connect_to_stalker():
    """Setup the connection to the Stalker database"""
    root = pathlib.Path(__file__).parent
    stalker_config_filepath = root / ".stalker_config.json"
    with stalker_config_filepath.open("r") as stalker_config_file:
        stalker_config = json.load(stalker_config_file)
    database_engine_settings = stalker_config.get("database_engine_settings")
    db.setup(settings=database_engine_settings)


class Login(Resource):
    def post(self):
        data = request.get_json()
        login = data.get('login')
        password = data.get('password')
        if not login:
            return {'message': 'Missing login parameter'}, 400
        if not password:
            return {'message': 'Missing password parameter'}, 400
        user = User.query.filter(
            or_(User.login == login, User.email == login)).first()
        if user and user.check_password(password):
            ret = {'access_token': create_access_token(identity=user.id)}
            return ret, 200



def main():
    connect_to_stalker()
    api.add_resource(Login, '/login')
    api.add_resource(ApiUser, '/user/<string:login>')
    api.add_resource(ApiUsers, '/users')
    app.run(port=5000, debug=True)


if __name__ == "__main__":
    main()
