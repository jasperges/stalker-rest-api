import stalker
from flask import request
from flask_jwt_extended import create_access_token
from flask_restful import Resource
from sqlalchemy import or_


class Login(Resource):
    def post(self):
        data = request.get_json()
        login = data.get('login')
        password = data.get('password')
        if not login:
            return {'message': 'Missing login parameter'}, 400
        if not password:
            return {'message': 'Missing password parameter'}, 400
        user = stalker.User.query.filter(
            or_(stalker.User.login == login,
                stalker.User.email == login)).first()
        if user and user.check_password(password):
            ret = {'access_token': create_access_token(identity=user.id)}
            return ret, 200
