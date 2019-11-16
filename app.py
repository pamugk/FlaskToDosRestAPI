from os import environ

import json
from database import db_session, init_db
from db_logic import *
from flask import Flask, jsonify, render_template, request, redirect, session, url_for
from flask_cors import CORS, cross_origin
from validation_logic import *
from serialization_logic import *

app = Flask(__name__)
app.secret_key = '6c131473-dcc5-4c44-9934-5526a9df4d02'
CORS(app)

init_db()
if __name__ == '__main__':
    app.run('localhost', 80, debug=True)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

@app.errorhandler(404)
def not_found(request):
    return "Page not found", 404

@app.route('/')
def home():
    return "That's the root of a Todos RESTful app server", 200

@app.route('/api/login', methods=['POST'])
def login_action():
    error = None

    if request.json['Login']:
        user = get_user_by_login(request.json['Login'])
        if not user:
            error = "There's no user with such login"
        elif (not request.json['Password'] or request.json['Password'].strip() == ''):
            error = "Password has to be provided"
        elif not check_user_password(user, request.json['Password']):
            error = "Wrong password"
        else:
            return user.generate_auth_token(), 200
    else:
        error = "Login has to provided"

    return error, 401

@app.route('/api/logout')
def logout():
    return "OK", 200

@app.route('/api/registration', methods=['POST'])
def registration_action():
    error = None
    code = 418

    if not request.json['Login']:
        error = "Login has to be set"
    elif not validate_login(request.json['Login']):
        error="Login is either empty or contains forbidden characters"
    elif get_user_by_login(request.json['Login']):
        error="This login is already taken"
    elif not request.json['Password']:
        error="Password has to be set"
    elif not validate_password(request.json['Password']):
        error="Password is either empty or contains forbidden characters"
    else:
        add_user(request.json['Login'], request.json['Password'])
        code = 200
    return 'Success' if error is None else error, code

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    user = User.verify_auth_token(request.args['token'])
    if not user:
        return 'Buzz off', 401

    return serialize_task_list(get_tasks_by_user_id(user.id)), 200

@app.route('/api/tasks', methods=['POST'])
def create_task():
    user = User.verify_auth_token(request.args['token'])
    if not user:
        return 'Buzz off', 401

    if not request.json['Title']:
       return "Title of task has to be set", 406
    if not validate_task_title(request.json['Title']):
        return "Title of task is either empty or contains forbidden symbols", 406
    if get_task_by_title(request.json['Title'], user.id) is not None:
        return "Task with this title is already exists", 406
    new_id = add_task(user.id, request.json['Title'], request.json['Description'])
    return json.dumps(new_id), 201

@app.route('/api/tasks/<id>', methods=['GET'])
def get_task(id):
    user = User.verify_auth_token(request.args['token'])
    if not user:
        return 'Buzz off', 401

    task= get_task_by_id(user.id, id)
    error = None
    code = 200
    if task[1]:
        if task[0] is None:
            error = "We're terribly sorry, but task with this ID wasn't found :("
            code = 404
        else:
            return serialize_single_task(task[0]), code
    else:
        error = "No-no-no, this task is not yours, so... buzz off"
        code = 403
    return error, code

@app.route('/api/tasks/<id>', methods=['PUT'])
def task_update(id):
    user = User.verify_auth_token(request.args['token'])
    if not user:
        return 'Buzz off', 401

    error = None
    code = None
    task = get_task_by_id(user.id, id)

    if task[0] is None:
        error = "Task not found"
        code = 404
    elif not task[1]:
        error = "WTF, you can't just go and edit task that does not belong to you :("
        code=403
    elif not request.json['Title']:
        error = "Title of task has to be set"
        code=400
    elif not validate_task_title(request.json['Title']):
        error = "Title of task is either empty or contains forbidden symbols"
        code=406
    else:
        suspectedTask = get_task_by_title(request.json['Title'], user.id)
        if suspectedTask is not None and suspectedTask.id != task[0].id:
            error = "Task with this title is already exists"
            code=406
        else:
            update_task(user.id, task[0], request.json['Title'], request.json['Description'], request.json['IsFinished'] == 'true')
            code=200
    return 'Success' if error is None else error, code

@app.route('/api/tasks/<id>', methods=['PATCH'])
def task_change_finished(id):
    user = User.verify_auth_token(request.args['token'])
    if not user:
        return 'Buzz off', 401

    error = None
    code = None
    task = get_task_by_id(user.id, id)
    success = False

    if task[0] is None:
        error = "Task not found"
        code = 404
    elif not request.json['IsFinished']:
        error = "Task status is missing"
        code=400
    elif not task[1]:
        error = "WTF, you can't just go and edit task that does not belong to you :("
        code=403
    else:
        finish_task(task[0], request.json['IsFinished'] == 'true')
        success = True
        code = 200
    return 'Success' if error is None else error, code

@app.route('/api/tasks/<id>', methods=['DELETE'])
def task_remove(id):
    user = User.verify_auth_token(request.args['token'])
    if not user:
        return 'Buzz off', 401

    if not is_users_task(user.id, id):
        return "You've got no rights to mess with this task", 403
    remove_task(user.id, id)
    return "Success", 200

@app.route('/api/user/me', methods=['GET'])
def userinfo():
    user = User.verify_auth_token(request.args['token'])
    return serialize_user_info(user), 200