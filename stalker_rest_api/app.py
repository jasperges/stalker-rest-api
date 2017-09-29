import pathlib
import json


from flask import Flask, request
from flask_restful import Resource, Api


from stalker import db, User, Project
from stalker.db.session import DBSession


app = Flask(__name__)
api = Api(app)


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


class ApiUser(Resource):
    def get(self, login):
        user = User.query.filter_by(login=login).first()
        if user:
            return format_user(user)
        return {'user': None}, 404

    def post(self, login):
        data = request.get_json()
        user = User(
            name=data['name'],
            email=data['email'],
            login=login,
            password=data['password'],
        )
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
    api.add_resource(ApiUser, '/user/<string:login>')
    api.add_resource(ApiUsers, '/users')
    app.run(port=5000, debug=True)


if __name__ == "__main__":
    main()
