import pathlib
import json
import logging


from flask import Flask
from flask import jsonify
from flask import request
from flask import render_template
from stalker import db
from stalker.db.session import DBSession
from stalker import User
from stalker import Project


app = Flask(__name__)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# Connect to Stalker test database
def connect_to_stalker():
    """Setup the connection to the Stalker database"""
    root = pathlib.Path(__file__).parent
    stalker_config_filepath = root / ".stalker_config.json"
    with stalker_config_filepath.open("r") as stalker_config_file:
        stalker_config = json.load(stalker_config_file)
    database_engine_settings = stalker_config.get("database_engine_settings")
    logger.debug("Database engine settings: %s", database_engine_settings)
    db.setup(settings=database_engine_settings)
    logger.debug("Connected to database")


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


@app.route('/')
def home():
    return render_template('index.html')

# POST /user data: {name:, login:, email:, password:,}
@app.route('/user', methods=['POST'])
def create_user():
    request_data = request.get_json()
    new_user = User(
        name=request_data['name'],
        login=request_data['login'],
        email=request_data['email'],
        password=request_data['password'],
    )
    DBSession.save(new_user)
    return jsonify(format_user(new_user))


# GET /user/<string:user_id>
@app.route('/user/<string:user_id>')
def get_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    if user:
        return jsonify(format_user(user))
    else:
        return jsonify({'message': "User not found"})


# GET /user
@app.route('/user')
def get_users():
    users = [format_user(user) for user in User.query.all()]
    return jsonify({"users": users})


# POST /user/<string:user_id>/project {name:, code:,}
@app.route('/user/<string:user_id>/project', methods=['POST'])
def create_project_for_user(user_id):
    request_data = request.get_json()
    new_project = Project(
        name=request_data['name'],
        code=request_data['code'],
    )
    user = User.query.filter_by(id=user_id).first()
    user.projects.append(new_project)
    DBSession.save(new_project)
    return jsonify(format_project(new_project))


# GET /user/<string:user_id>/project
@app.route('/user/<string:user_id>/project')
def get_projects_from_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'message': "User not found"})
    projects = [format_project(project) for project in user.projects]
    return jsonify({"projects": projects})


# GET /project
@app.route('/project')
def get_projects():
    projects = [format_project(project) for project in Project.query.all()]
    return jsonify({"projects": projects})


def main():
    connect_to_stalker()
    logger.debug("Serving on localhost:5000")
    app.run(port=5000)


if __name__ == "__main__":
    main()
