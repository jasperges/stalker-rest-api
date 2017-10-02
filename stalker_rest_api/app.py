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


def format_user(user):
    """Format a user for json"""
    return {"id": user.id,
            "name": user.name,
            "login": user.login,
            "email": user.email}


def format_project(project):
    """Format a project for json"""
    return {"id": project.id,
            "name": project.name,
            "code": project.code}


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
            return format_user(user)
        else:
            return {'message': 'User is not authorized to view information of other users'}, 401

    def post(self, login):
        data = request.get_json()
        if User.query.filter(or_(User.login==login, User.email==data['email'])).first():
            return {'message': 'A user with this login or email already exists'}, 400
        user = User(
            name=data['name'],
            email=data['email'],
            login=login,
            password=data['password'],
        )
        DBSession.save(user)
        return format_user(user), 201

    def put(self, login):
        data = request.get_json()
        if not User.query.filter_by(login=login).first():
            if data.get('email') and User.query.filter_by(email=data['email']).first():
                return {'message': 'A user with this email already exists'}, 400
            if not data.get('name') or not data.get('email') or not data.get('password'):
                return {'message': 'For new users name, email and password are required'}, 400
            user = User(
                name=data['name'],
                email=data['email'],
                login=login,
                password=data['password'],
            )
        else:
            if data.get('email') and User.query.filter(User.email==data['email'], User.login!=login).first():
                return {'message': 'A user with this email already exists (email not unique)'}, 400
            if data.get('login') and data['login'] != login and User.query.filter_by(login=data['login']).first():
                return {'message': 'A user with login \'{}\' already exists'.format(data['login'])}, 400
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
        return format_user(user), 201

    def delete(self, login):
        user = User.query.filter_by(login=login).first()
        if not user:
            return {'user': None}, 404
        DBSession.delete(user)
        DBSession.commit()
        return {'message': 'Deleted user \'{}\''.format(login)}


class ApiUsers(Resource):
    def get(self):
        users = [format_user(user) for user in User.query.all()]
        if users:
            return users
        return {'users': None}, 404


def main():
    connect_to_stalker()
    api.add_resource(Login, '/login')
    api.add_resource(ApiUser, '/user/<string:login>')
    api.add_resource(ApiUsers, '/users')
    app.run(port=5000, debug=True)


if __name__ == "__main__":
    main()
