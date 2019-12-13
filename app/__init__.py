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
from sqlalchemy import desc, asc
import random



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

@app.route("/getuser", methods=['GET'])
@login_required
def getuser():
    avatars = [
        "https://img.icons8.com/plasticine/100/000000/person-female.png",
        "https://img.icons8.com/plasticine/100/000000/person-male.png"
    ]
    object = {
        "user_id": current_user.id,
        "user_name": current_user.username,
        "avatar_url": current_user.avatar_url
    }
    # if current_user.avatar_url:
    #     object["avatar_url"] = current_user.avatar_url
    # else:
    #     oject["avatar_url"] = avatars[random.randint(0, 1)]
    object["avatar_url"] = current_user.avatar_url if current_user.avatar_url else avatars[random.randint(0, 1)]
    # Get User's Teams
    if len(current_user.teams) > 0:
        jsonized_team_objects_list = []
        for team in current_user.teams:
            if team.status != "deleted":
                members = []
                for user in team.users:
                    members.append(user.as_dict())
                team = team.as_dict()
                team.update({'members': members})
                jsonized_team_objects_list.append(team)
        object["teams"] = jsonized_team_objects_list

    # Get User's Projects
    if len(current_user.projects) > 0:
        jsonized_project_objects_list = []
        for project in current_user.projects:
            if project.status != "deleted":
                jsonized_project_objects_list.append(project.as_dict())
        object["projects"] = jsonized_project_objects_list

    return jsonify(object)

@app.route("/getuser/all", methods=['GET'])
@login_required
def get_all_user():
    avatars = [
        "https://img.icons8.com/plasticine/100/000000/person-female.png",
        "https://img.icons8.com/plasticine/100/000000/person-male.png"
    ]
    users = User.query.filter_by(status='active').filter(User.id!=1).all()
    jsonized_user_objects_list = []
    userObject = {}
    for user in users:
        userObject = {
            "id": user.id,
            "username": user.username,
        }

        if user.email:
            userObject["email"] = user.email 
        else:
            userObject['email'] = user.origin

        if user.avatar_url:
            userObject["avatar_url"] = user.avatar_url
        else: 
            userObject["avatar_url"] = avatars[random.randint(0, 1)]

        jsonized_user_objects_list.append(userObject)
    return jsonify(success=True, users=jsonized_user_objects_list)

@app.route("/user/<id>/getboards", methods=['GET', 'POST'])
@login_required
def get_boards(id):
    current_boards = current_user.boards.filter(Board.status != "deleted").order_by(asc(Board.timestamp)).all()
    if len(current_boards) < 1:
        return jsonify(success=False, error="There is no board")
    jsonized_board_objects_list = []
    for board in current_boards:
        jsonized_board_objects_list.append(board.as_dict())
    return jsonify(success=True, boards=jsonized_board_objects_list)

@app.route("/project/<id>/getdata", methods=['GET', 'POST'])
@login_required
def get_project_data(id):
    current_proj = Project.query.filter_by(id = id, creator_id = current_user.id, status = 'active').first()
    if not current_proj:
        return jsonify(success=False, error="There is no project")
    current_boards = current_proj.boards.filter(Board.status != "deleted").order_by(asc(Board.timestamp)).all()
    print('current_boards', current_boards)
    if len(current_boards) < 1:
        return jsonify(success=False, error="There is no board")
    jsonized_board_objects_list = []
    for board in current_boards:
        jsonized_board_objects_list.append(board.as_dict())
    return jsonify(success=True, projects=current_proj.as_dict(), boards=jsonized_board_objects_list)

@app.route("/team/<id>/getdata", methods=['GET', 'POST'])
@login_required
def get_team_data(id):
    current_team = Team.query.filter_by(id = id, status = 'active').first()
    if not current_team:
        return jsonify(success=False, error="There is no team")
    current_boards = current_team.boards.filter(Board.status != "deleted").order_by(asc(Board.timestamp)).all()
    # print("currentBoard", current_boards)
    jsonized_board_objects_list = []
    if len(current_boards) > 0:
        for board in current_boards:
            jsonized_board_objects_list.append(board.as_dict())
            
    avatars = [
        "https://img.icons8.com/plasticine/100/000000/person-female.png",
        "https://img.icons8.com/plasticine/100/000000/person-male.png"
    ]
    jsonized_user_objects_list = []
    # print("sdfsdfsdf", current_team.users)
    for user in current_team.users:
        userObject = {
            "id": user.id,
            "username": user.username,
        }

        if user.email:
            userObject["email"] = user.email 
        else:
            userObject['email'] = user.origin

        if user.avatar_url:
            userObject["avatar_url"] = user.avatar_url
        else: 
            userObject["avatar_url"] = avatars[random.randint(0, 1)]

        jsonized_user_objects_list.append(userObject)

    return jsonify(
        success=True,
        team=current_team.as_dict(),
        boards=jsonized_board_objects_list,
        users=jsonized_user_objects_list
    )

@app.route("/createproject", methods=['GET', 'POST'])
@login_required
def create_project():
    if request.method == "POST":
        dt = request.get_json()
        new_project = Project(
            name = dt['name'],
            creator_id = current_user.id,
        )
        db.session.add(new_project)

        if dt["project_type"] == "personal":
            new_project.project_type = "personal"
            new_project.users.append(current_user)
            
        if dt["project_type"] == "team" and dt['team_id']:
            new_project.team_id = dt['team_id']
            new_project.project_type = "team"
            current_team = Team.query.get(dt['team_id'])
            if current_team.status == "active":
                current_team.projects.append(new_project)

        db.session.commit()
        return jsonify(success=True, team=new_project.as_dict())
    return jsonify(success=False)

@app.route("/createteam", methods=['GET', 'POST'])
@login_required
def create_team():
    if request.method == "POST":
        dt = request.get_json()
        new_team = Team(
            name = dt['name'],
            creator_id = current_user.id,
        )
        db.session.add(new_team)
        new_team.users.append(current_user)

        if len(dt['users']) > 0:
            for id in dt['users']:
                new_user = User.query.get(id)
                if not new_user in new_team.users:
                    new_team.users.append(new_user)

        db.session.commit()
        print(new_team)
        return jsonify(success=True, team=new_team.as_dict())
    return jsonify(success=False)

@app.route("/team/<id>/editteam", methods=['GET', 'POST'])
@login_required
def edit_team(id):
    if request.method == "POST":
        dt = request.get_json()
        current_team = Team.query.filter_by(id=id, status = "active").first()
        if not current_team:
            return jsonify(success=False, error=f"There is no active team with id:{id}")
        if current_team.creator_id != current_user.id:
            return jsonify(success=False, error=f"Current User is not the creator of team #{id}")

        if dt["type"] == "delete":
            current_team.status = "deleted"
            if len(current_team.boards.all()) > 0:
                for board in current_team.boards.all():
                    board.status = "deleted"
                    board.delete_all()

        if dt["type"] == "edit":
            current_team.name = dt['name']
            for id in dt['users']:
                new_user = User.query.filter_by(id = id, status = "active").first()
                if new_user and (not new_user in current_team.users):
                    current_team.users.append(new_user)

        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False)

@app.route("/project/<id>/", methods=['GET', 'POST'])
@login_required
def edit_project(id):
    if request.method == "POST":
        dt = request.get_json()
        current_project = Project.query.filter_by(id = id, status = "active").first()
        if not current_project:
            return jsonify(success=False, error=f"There is no active project with id:{id}")
        if current_project.creator_id != current_user.id:
            return jsonify(success=False, error=f"Current User is not the creator of projet #{id}")

        if dt["type"] == "delete":
            current_project.status = "deleted"
            if len(current_project.boards.all()) > 0:
                for board in current_project.boards.all():
                    board.status = "deleted"
                    board.delete_all()

        if dt["type"] == "edit":
            current_project.name = dt['name']
            for id in dt['users']:
                new_user = User.query.filter_by(id = id, status = "active").first()
                if new_user and (not new_user in current_project.users):
                    current_project.users.append(new_user)

        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False)

@app.route("/createboard", methods=['GET', 'POST'])
@login_required
def create_board():
    if request.method == "POST":
        dt = request.get_json()
        new_board = Board(
            name = dt['name'],
            creator_id = current_user.id
        )
        db.session.add(new_board)
        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False)

@app.route("/board/<id>", methods=['GET', 'POST'])
@login_required
def update_board(id):
    if request.method == 'POST':
        dt = request.get_json()
        current_board = Board(id = id).check_id()
        if not current_board:
            return jsonify(success=False, error=f"There is no board with id#{id}")
        if current_board.creator_id != current_user.id:
            return jsonify(success=False, error=f"Current user is not the creator of board #{id}")
        if dt['type'] == 'edit':
            current_board.name = dt['name']
        if dt['type'] == 'delete':
            current_board.status = "deleted"
            current_board.delete_all()
        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False)
    

@app.route("/board/<id>/delete", methods=['GET', 'POST'])
@login_required
def delete_board(id):
    if request.method == 'POST':
        dt = request.get_json()
        current_board = Board(id = id).check_id()
        if not current_board:
            return jsonify(success=False, error=f"There is no board with id#{id}")
        if current_board.creator_id != current_user.id:
            return jsonify(success=False, error=f"Current user is not the creator of board #{id}")
        current_board.status="deleted"
        current_board.delete_all()
        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False)


@app.route("/board/<id>/createtask", methods=['GET', 'POST'])
@login_required
def create_task(id):
    if request.method == 'POST':
        dt = request.get_json()
        current_board = Board(id = id).check_id()
        if not current_board:
            return jsonify(success=False, error=f"There is no board with id#{id}")
        new_task = Task(
            body = dt['body'],
            note = dt['note'],
            priority = dt['priority'],
            duedate = datetime.strptime(dt['duedate'], "%Y-%m-%dT%H:%M:%S.%fZ"),
            board_id = id,
            creator_id = current_user.id
        )
        db.session.add(new_task)

        for id in dt['assignees']:
            if type(id) is int:
                new_user = User.query.get(id) 
                if new_user:
                    if not new_task in new_user.assigned_tasks:
                        new_user.assigned_tasks.append(new_task)
            else: 
                current_user.assigned_tasks.append(new_task)

        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False)


@app.route("/board/<id>/gettasks", methods=['GET', 'POST'])
@login_required
def get_tasks(id):
    current_board = Board(id = id).check_id()
    if not current_board:
        return jsonify(success=False, error=f"There is no board with id#{id}")
    if current_board.tasks:
        tasks = current_board.tasks.filter(Task.status != "deleted").order_by(asc(Task.timestamp)).all()
        jsonized_task_objects_list = []
        for task in tasks:
            jsonized_task_objects_list.append(task.as_dict())
        return jsonify(success=True, tasks=jsonized_task_objects_list)
    return jsonify(success=True, tasks='' )

@app.route("/task/<id>", methods=['GET', 'POST'])
@login_required
def update_tasks(id):
    if request.method == 'POST':
        dt = request.get_json()
        current_task = Task(id = id).check_id()
        if not current_task:
            return jsonify(success=False, error=f"There is no task with id#{id}")
        if dt['type'] == "update":
            if dt['checked'] == True:
                current_task.status = "finished"
            elif dt['checked'] == False:
                current_task.status = "unfinished"
        if dt['type'] == "edit":
            current_task.body = dt['body'],
            current_task.note = dt['note'],
            current_task.priority = dt['priority'],
            current_task.duedate = datetime.strptime(dt['duedate'], "%Y-%m-%dT%H:%M:%S.%fZ"),
            current_task.assignee_id = dt['assignees'],
        if dt['type'] == "delete":
            current_task.status = dt['status']

        db.session.commit()
        return jsonify(success=True, task=current_task.as_dict())    
    return jsonify(success=False)    

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