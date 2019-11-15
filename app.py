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
    app.run('localhost', 5000, debug=True)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

@app.errorhandler(404)
def not_found():
    return "Page not found", 404

@app.route('/api/login', methods=['POST'])
def login_action():
    error = None
    code = 401

    if request.form['login']:
        user = get_user_by_login(request.form['login'])
        if not user:
            error = "There's no user with such login"
        elif (not request.form['password'] or request.form['login'].strip() == ''):
            error = "Password has to be provided"
        elif not check_user_password(user, request.form['password']):
            error = "Wrong password"
        else:
            session['user_id'] = user.id
            code = 200
    else:
        error = "Login has to provided"

    return 'Success' if error is None else error, code

@app.route('/api/logout')
def logout():
    session.pop('user_id')
    return "OK", 200

@app.route('/api/registration', methods=['POST'])
def registration_action():
    error = None
    code = 418

    if not request.form['login']:
        error = "Login has to be set"
    elif not validate_login(request.form['login']):
        error="Login is either empty or contains forbidden characters"
    elif get_user_by_login(request.form['login']):
        error="This login is already taken"
    elif not request.form['password']:
        error="Password has to be set"
    elif not validate_password(request.form['password']):
        error="Password is either empty or contains forbidden characters"
    else:
        add_user(request.form['login'], request.form['password'])
        code = 200
    return 'Success' if error is None else error, code

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    if 'user_id' not in session:
        return 'Buzz off', 401

    user_id = session['user_id']
    return serialize_task_list(get_tasks_by_user_id(user_id)), 200

@app.route('/api/tasks', methods=['POST'])
def create_task():
    if 'user_id' not in session:
        return 'Buzz off', 401

    user_id = session['user_id']

    if not request.form['title']:
       return "Title of task has to be set", 406
    if not validate_task_title(request.form['title']):
        return "Title of task is either empty or contains forbidden symbols", 406
    if get_task_by_title(request.form['title'], user_id) is not None:
        return "Task with this title is already exists", 406
    add_task(user_id, request.form['title'], request.form['description'])
    return 'Success', 201

@app.route('/api/tasks/<id>', methods=['GET'])
def get_task(id):
    if 'user_id' not in session:
        return 'Buzz off', 401

    user_id = session['user_id']
    task=get_task_by_id(user_id, id)
    error = None
    code = 200
    print(id)
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
    if 'user_id' not in session:
        return 'Buzz off', 401

    error = None
    code = None
    user_id = session['user_id']
    user = get_user_by_id(user_id)
    task = get_task_by_id(user_id, id)

    if task[0] is None:
        error = "Task not found"
        code = 404
    elif not task[1]:
        error = "WTF, you can't just go and edit task that does not belong to you :("
        code=403
    elif not request.form['title']:
        error = "Title of task has to be set"
        code=400
    elif not validate_task_title(request.form['title']):
        error = "Title of task is either empty or contains forbidden symbols"
        code=406
    else:
        suspectedTask = get_task_by_title(request.form['title'], session['user_id'])
        if suspectedTask is not None and suspectedTask.id != task[0].id:
            error = "Task with this title is already exists"
            code=406
        else:
            update_task(user_id, task[0], request.form['title'], request.form['description'], request.form['finished'] == 'true')
            code=200
    return 'Success' if error is None else error, code

@app.route('/api/tasks/<id>', methods=['PATCH'])
def task_change_finished(id):
    if 'user_id' not in session:
        return 'Buzz off', 401

    error = None
    code = None
    user_id = session['user_id']
    user = get_user_by_id(user_id)
    task = get_task_by_id(user_id, id)
    success = False

    if task[0] is None:
        error = "Task not found"
        code = 404
    elif not request.form['finished']:
        error = "Task status is missing"
        code=400
    elif not task[1]:
        error = "WTF, you can't just go and edit task that does not belong to you :("
        code=403
    else:
        finish_task(task[0], request.form['finished'] == 'true')
        success = True
        code = 200
    return 'Success' if error is None else error, code

@app.route('/api/tasks/<id>', methods=['DELETE'])
def task_remove(id):
    if 'user_id' not in session:
        return 'Buzz off', 401

    user_id = session['user_id']
    if not is_users_task(user_id, id):
        return "You've got no rights to mess with this task", 403
    remove_task(user_id, id)
    return "Success", 200
