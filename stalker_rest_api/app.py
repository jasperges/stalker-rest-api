import pathlib
import json


from flask import Flask
from flask_restful import Resource, Api


from stalker import db
from stalker.db.session import DBSession
from stalker import User
from stalker import Project


app = Flask(__name__)


# Connect to Stalker test database
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


def main():
    connect_to_stalker()
    app.run(port=5000)


if __name__ == "__main__":
    main()
