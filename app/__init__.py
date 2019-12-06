from flask import Flask, redirect, url_for, flash, render_template, jsonify, request
from flask_login import login_required, login_user, logout_user, current_user
from .config import Config
from .models import db, login_manager, Token, User, Board, Task, Project, Team
from .oauth import blueprint
from .cli import create_db
from flask_migrate import Migrate
from flask_cors import CORS, cross_origin
import uuid
import os
from flask_moment import Moment
from datetime import datetime



app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
moment = Moment(app)



app.register_blueprint(blueprint, url_prefix="/login")


app.cli.add_command(create_db)
db.init_app(app)

migrate = Migrate(app, db)
login_manager.init_app(app)


@app.route("/")
def index():
    return render_template("home.html")

@app.route("/signup", methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        print("running create user")
        dt = request.get_json()
        user = User(email = dt['email']).check_email()
        print("user query result", user)
        if user:
            print('user true')
            return jsonify({'success': False, 'error': "Email's already taken"})
        if dt['username'] == '' and dt['password'] == '':
            return jsonify({'success': False, 'error': "No username or password sent"})
        user = User(
            email = dt['email'],
            username = dt['username'],
            origin = 'email'
        )
        user.set_password(dt['password'])
        db.session.add(user)
        db.session.commit()
        return jsonify({'success': True})

    return jsonify({'success': False, 'error': 'no sent data'})

@app.route("/login", methods=['GET', 'POST'])
@cross_origin(allow_headers=['Content-Type'])
def login():
    if request.method == 'POST':
        dt = request.get_json()
        user = User(email = dt['email']).check_email()
        if user:
            if user.origin != 'email':
                return jsonify({'success': False, 'error': "Email's not found"})    
            if not user.check_password(dt['password']):
                return jsonify({'success': False, 'error': "Incorrect password"})
            
            login_user(user)
            token = Token.query.filter_by(user_id=user.id).first()
            if not token:
                token = Token(user_id=current_user.id, uuid=str(uuid.uuid4().hex))
                db.session.add(token)
                db.session.commit()
            print("login success", token)
            return jsonify(success=True, user={
                'id': current_user.id,
                'username': current_user.username
            }, token=token.uuid)
    return jsonify({'success': False, 'error': 'no sent data'})

@app.route("/getuser", methods=['GET'])
@login_required
def getuser():
    return jsonify({"user_id": current_user.id,
                    "user_name": current_user.username,
                    })

@app.route("/logout", methods=['GET'])
@login_required
def logout():
    token = Token.query.filter_by(user_id=current_user.id).first()
    print('LOG OUT TOKEN', token)
    if token:
        db.session.delete(token)
        db.session.commit()
    logout_user()
    flash("You have logged out")
    return jsonify({
        "success":True
    })

@app.route("/createboard", methods=['GET', 'POST'])
@login_required
def create_board():
    pass

@app.route("/board/<id>/createtask", methods=['GET', 'POST'])
@login_required
def create_task(id):
    if request.method == 'POST':
        dt = request.get_json()
        current_board = Board(id = id).check_id()
        print('current_board:', current_board)
        if not current_board:
            return jsonify(success=False, error=f"There is no board with id#{id}")
        new_task = Task(
            body = dt['body'],
            note = dt['note'],
            priority = dt['priority'],
            duedate = datetime.strptime(dt['duedate'], "%Y-%m-%dT%H:%M:%S.%fZ"),
            board_id = id,
            user_id = dt['assignees'],
            creator_id = current_user.id
        )
        db.session.add(new_task)
        db.session.commit()
        print(new_task)
        return jsonify(success=True)
    return jsonify(success=False)

# @app.route("/")

# @app.route('/user/id', methods=['GET'])
# def user():
#     excerpts = Excerpt.query.all()
#     jsonized_excerpt_objects_list = []
#     for excerpt in excerpts:
#         jsonized_excerpt_objects_list.append(excerpt.as_dict())

#     return jsonify(jsonized_excerpt_objects_list)

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request. %s', e)
    return "An internal error occured", 500