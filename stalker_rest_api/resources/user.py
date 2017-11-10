import stalker
from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from marshmallow import Schema, fields, post_load
from sqlalchemy import or_
from stalker.db.session import DBSession


class UserSchema(Schema):
    user_id = fields.Integer()
    name = fields.String(required=True)
    login = fields.String(required=True)
    email = fields.Email(required=True)
    password = fields.String(required=True)

    @post_load
    def make_user(self, data):
        return stalker.User(**data)


class User(Resource):
    @jwt_required
    def get(self, login):
        identity = get_jwt_identity()
        user = stalker.User.query.filter_by(login=login).first()
        if not user:
            return {'user': None}, 404
        if user.id == identity:
            data, errors = UserSchema(exclude=('password', )).dump(user)
            if errors:
                return errors
            return data, 200
        else:
            return {
                'message':
                'User is not authorized to view information of other users'
            }, 401

    def post(self, login):
        data = request.get_json()
        user, errors = UserSchema().load(data)
        if errors:
            return errors
        if stalker.User.query.filter(
                or_(stalker.User.login == login,
                    stalker.User.email == data['email'])).first():
            return {
                'message': 'A user with this login or email already exists'
            }, 400
        DBSession.save(user)
        user_data, errors = UserSchema(exclude=('password', )).dump(user)
        if errors:
            return errors
        return user_data, 201

    def put(self, login):
        data = request.get_json()
        if not stalker.User.query.filter_by(login=login).first():
            if data.get('email') and stalker.User.query.filter_by(
                    email=data['email']).first():
                return {
                    'message': 'A user with this email already exists'
                }, 400
            schema = UserSchema()
            result = schema.load(data)
            if result.errors:
                return result.errors
            user = result.data
        else:
            if data.get('email') and stalker.User.query.filter(
                    stalker.User.email == data['email'],
                    stalker.User.login != login).first():
                return {
                    'message':
                    'A user with this email already exists (email not unique)'
                }, 400
            if data.get(
                    'login'
            ) and data['login'] != login and stalker.User.query.filter_by(
                    login=data['login']).first():
                return {
                    'message': 'A user with this login already exists'
                }, 400
            user = stalker.User.query.filter_by(login=login).first()
            if data.get('login'):
                user.login = data['login']
            if data.get('name'):
                user.name = data['name']
            if data.get('email'):
                user.email = data['email']
            if data.get('password'):
                user.password = data['password']
        DBSession.save(user)
        data, errors = UserSchema(exclude=('password', )).dump(user)
        return data, 201

    def delete(self, login):
        user = stalker.User.query.filter_by(login=login).first()
        if not user:
            return {'user': None}, 404
        DBSession.delete(user)
        DBSession.commit()
        data, errors = UserSchema(exclude=('password', )).dump(user)
        if errors:
            return errors
        return {'message': 'Deleted user', 'user': data}


class UserList(Resource):
    def get(self):
        users = [user for user in stalker.User.query.all()]
        if users:
            data, errors = UserSchema(
                exclude=('password', ), many=True).dump(users)
            if errors:
                return errors
            return data
        return {'users': None}, 404
