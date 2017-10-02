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
app.secret_key = 'secretkey'    # FIXME: just for testing
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


class UserSchema(Schema):
    user_id = fields.Integer()
    name = fields.String(required=True)
    login = fields.String(required=True)
    email = fields.Email(required=True)
    password = fields.String(required=True)

    @post_load
    def make_user(self, data):
        return User(**data)


class Login(Resource):
    def post(self):
        data = request.get_json()
        login = data.get('login')
        password = data.get('password')
        if not login:
            return {'message': 'Missing login parameter'}, 400
        if not password:
            return {'message': 'Missing password parameter'}, 400
        user = User.query.filter(or_(User.login==login, User.email==login)).first()
        if user and user.check_password(password):
            ret = {'access_token': create_access_token(identity=user.id)}
            return ret, 200


class ApiUser(Resource):
    @jwt_required
    def get(self, login):
        identity = get_jwt_identity()
        user = User.query.filter_by(login=login).first()
        if not user:
            return {'user': None}, 404
        if user.id == identity:
            data, errors = UserSchema(exclude=('password',)).dump(user)
            if errors:
                return errors
            return data, 200
        else:
            return {'message': 'User is not authorized to view information of other users'}, 401

    def post(self, login):
        data = request.get_json()
        user, errors = UserSchema().load(data)
        if errors:
            return errors
        if User.query.filter(or_(User.login==login, User.email==data['email'])).first():
            return {'message': 'A user with this login or email already exists'}, 400
        DBSession.save(user)
        user_data, errors = UserSchema(exclude=('password',)).dump(user)
        if errors:
            return errors
        return user_data, 201

    def put(self, login):
        data = request.get_json()
        if not User.query.filter_by(login=login).first():
            if data.get('email') and User.query.filter_by(email=data['email']).first():
                return {'message': 'A user with this email already exists'}, 400
            schema = UserSchema()
            result = schema.load(data)
            if result.errors:
                return result.errors
            user = result.data
        else:
            if data.get('email') and User.query.filter(User.email==data['email'], User.login!=login).first():
                return {'message': 'A user with this email already exists (email not unique)'}, 400
            if data.get('login') and data['login'] != login and User.query.filter_by(login=data['login']).first():
                return {'message': 'A user with this login already exists'}, 400
            user = User.query.filter_by(login=login).first()
            if data.get('login'):
                user.login = data['login']
            if data.get('name'):
                user.name = data['name']
            if data.get('email'):
                user.email = data['email']
            if data.get('password'):
                user.password = data['password']
        DBSession.save(user)
        data, errors = UserSchema(exclude=('password',)).dump(user)
        return data, 201

    def delete(self, login):
        user = User.query.filter_by(login=login).first()
        if not user:
            return {'user': None}, 404
        DBSession.delete(user)
        DBSession.commit()
        data, errors = UserSchema(exclude=('password',)).dump(user)
        if errors:
            return errors
        return {'message': 'Deleted user', 'user': data}


class ApiUsers(Resource):
    def get(self):
        users = [user for user in User.query.all()]
        if users:
            data, errors = UserSchema(exclude=('password',), many=True).dump(users)
            if errors:
                return errors
            return data
        return {'users': None}, 404


def main():
    connect_to_stalker()
    api.add_resource(Login, '/login')
    api.add_resource(ApiUser, '/user/<string:login>')
    api.add_resource(ApiUsers, '/users')
    app.run(port=5000, debug=True)


if __name__ == "__main__":
    main()
