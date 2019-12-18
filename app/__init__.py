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
import re



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
            origin = 'email',
            role_id = 2,
        )
        user.set_password(dt['password'])
        db.session.add(user)
        db.session.commit()

        new_board = Board(name="To-Do", creator_id=user.id, user_order=1)
        db.session.add(new_board)

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
        "user": {
            "id": current_user.id,
            "user_name": current_user.username,
            "avatar_url": current_user.avatar_url,
            "email": current_user.email,
            "origin": current_user.origin,
        }
    }

    object["user"]["avatar_url"] = current_user.avatar_url if current_user.avatar_url else avatars[random.randint(0, 1)]
    
    # Get User's Boards
    current_boards = current_user.boards\
        .filter(Board.status != "deleted", Board.team_id==None, Board.project_id==None)\
            .order_by(asc(Board.user_order)).all()
    if len(current_boards) > 0:
        boardList, boards = [], {}
        for board in current_boards:
            boards[f"board-{board.id}"] = board.as_dict()
            boardList.append(f"board-{board.id}")
        object["boards"] = boards
        object["boardList"] = boardList

    # Get User's Teams
    if len(current_user.teams) > 0:
        teamList, teams = [], {}
        for team in current_user.teams:
            if team.status != "deleted":
                teams[f"team-{team.id}"] = team.as_dict()
                members = []
                userObject = {}
                for user in team.users:
                    userObject = {
                        "id": user.id,
                        "username": user.username,
                    }
                    userObject["email"] = user.email if user.email else user.origin
                    userObject["avatar_url"] = user.avatar_url if user.avatar_url else avatars[random.randint(0, 1)]
                    members.append(userObject)
                teams[f"team-{team.id}"]['members'] = members
                teamList.append(f"team-{team.id}")
        object["teams"] = teams
        object["teamList"] = teamList

    # Get User's Projects
    if len(current_user.projects) > 0:
        projList, projs = [], {}
        for project in current_user.projects:
            if project.status != "deleted" and project.team_id == None:
                projs[f"project-{project.id}"] = project.as_dict()
                projList.append(f"project-{project.id}")
        object["projects"] = projs
        object["projectList"] = projList
        

    # Get all users' info:
    users = User.query.filter(User.id!=1, User.status!='deleted').all()
    jsonized_user_objects_list = []
    userObject = {}
    for user in users:
        userObject = {
            "id": user.id,
            "username": user.username,
        }
        userObject["email"] = user.email if user.email else user.origin
        userObject["avatar_url"] = user.avatar_url if user.avatar_url else avatars[random.randint(0, 1)]
        jsonized_user_objects_list.append(userObject)

    object["users"] = jsonized_user_objects_list

    return jsonify(object)

@app.route("/user/<id>/getboards", methods=['GET'])
@login_required
def get_boards(id):
    current_boards = current_user.boards\
        .filter(Board.status != "deleted", Board.team_id==None, Board.project_id==None)\
            .order_by(asc(Board.timestamp)).all()
    if len(current_boards):
        boardList, boards = [], {}
        for board in current_boards:
            boards[f"board-{board.id}"] = board.as_dict()
            boardList.append(f"board-{board.id}")
    return jsonify(success=True, boards=boards, boardList=boardList)

@app.route("/project/<id>/getdata", methods=['GET'])
@login_required
def get_project_data(id):
    current_project = Project.query.filter_by(id = id, status = 'active').first()
    if not current_project:
        return jsonify(success=False, error="There is no project")
    current_boards = current_project.boards.filter(Board.status != "deleted").order_by(asc(Board.project_order)).all()
    print('current_boards', current_boards)
    if len(current_boards) < 1:
        return jsonify(success=False, error="There is no board")
    boardList, boards = [], {}
    for board in current_boards:
        boards[f"board-{board.id}"] = board.as_dict()
        boardList.append(f"board-{board.id}")
    return jsonify(success=True, project=current_project.as_dict(), boards=boards, boardList=boardList)

@app.route("/team/<id>/getdata", methods=['GET'])
@login_required
def get_team_data(id):
    current_team = Team.query.filter_by(id = id, status = 'active').first()
    if not current_team:
        return jsonify(success=False, error="There is no team")
    avatars = [
        "https://img.icons8.com/plasticine/100/000000/person-female.png",
        "https://img.icons8.com/plasticine/100/000000/person-male.png"
    ]
    jsonized_user_objects_list = []
    current_projects = current_team.projects.filter(Project.status != "deleted").order_by(asc(Project.timestamp)).all()
    # print("currentBoard", current_boards)
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
    current_team = current_team.as_dict()
    current_team['members'] = jsonized_user_objects_list        
    projectList, projects = [], {}
    if len(current_projects) > 0:
        for project in current_projects:
            projects[f"project-{project.id}"] = project.as_dict()
            projectList.append(f"project-{project.id}")
        current_team["projectList"] = projectList

    # print("sdfsdfsdf", current_team.users)

    return jsonify(
        success=True,
        team=current_team,
        projects=projects,
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
        return jsonify(success=True, project=new_project.as_dict())
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

        new_project = Project(
            name=dt['projectname'] or "Default Project",
            project_type="team",
            creator_id=current_user.id, 
            team_id=new_team.id
        )
        db.session.add(new_project)
        db.session.commit()
        if dt['projecttype'] == "todo":
            new_board_1 = Board(name="To-Do", creator_id=current_user.id, project_id=new_project.id, project_order=1)
            new_board_2 = Board(name="Doing", creator_id=current_user.id, project_id=new_project.id, project_order=2)
            new_board_3 = Board(name="Done", creator_id=current_user.id, project_id=new_project.id, project_order=3)
            db.session.add(new_board_1)
            db.session.add(new_board_2)
            db.session.add(new_board_3)

        elif dt['projecttype'] == "user":
            for i, user in enumerate(new_team.users):
                new_board = Board(name=user.username, creator_id=current_user.id, project_id=new_project.id, project_order=i+1)
                db.session.add(new_board)
        elif dt['projecttype'] == "none":
            new_board = Board(name="To-Do", creator_id=current_user.id, project_id=new_project.id, project_order=1)
            db.session.add(new_board)
        
        db.session.commit()

        print(new_team)
        return jsonify(success=True, team=new_team.as_dict(), project=new_project.as_dict())
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

        if dt["type"] == "delete" and current_team.creator_id == current_user.id:
                current_team.status = "deleted"
                current_team.delete_all()

        if dt["type"] == "edit":
            current_team.name = dt['name']
            for id in dt['users']:
                new_user = User.query.filter_by(id = id, status = "active").first()
                if new_user and (not new_user in current_team.users):
                    current_team.users.append(new_user)

        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False)

@app.route("/project/<id>", methods=['GET', 'POST'])
@login_required
def edit_project(id):
    if request.method == "POST":
        dt = request.get_json()
        current_project = Project.query.filter_by(id = id, status = "active").first()
        if not current_project:
            return jsonify(success=False, error=f"There is no active project with id:{id}")
        if current_project.creator_id != current_user.id:
            return jsonify(success=False, error=f"Current User is not the creator of projet #{id}")

        if dt["type"] == "delete" and current_project.creator_id == current_user.id:
            current_project.status = "deleted"
            current_project.delete_all()

        if dt["type"] == "edit":
            current_project.name = dt['name']
            # for id in dt['users']:
            #     new_user = User.query.filter_by(id = id, status = "active").first()
            #     if new_user and (not new_user in current_project.users):
            #         current_project.users.append(new_user)

        db.session.commit()
        
        current_boards = current_project.boards.filter(Board.status != "deleted").order_by(asc(Board.project_order)).all()
        if len(current_boards) < 1:
            return jsonify(success=True, project=current_project.as_dict())
        boardList = []
        for board in current_boards:
            boardList.append(f"board-{board.id}")
        current_project = current_project.as_dict()
        current_project["boardList"] = boardList

        return jsonify(success=True, project=current_project.as_dict())
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
        if dt["type"]=="team":
            new_board.team_id = dt["team"]
        if dt["type"]=="project":
            new_board.project_id = dt["project"]
            last_board = Project.query.get(dt["project"]).boards\
                .filter(Board.status=="active").order_by(desc(Board.project_order)).first()
            if last_board and last_board.project_order != None:
                new_board.project_order = int(last_board.project_order) + 1
            else: new_board.project_order = 1

        elif dt["type"]=="personal":
            last_board = current_user.boards\
                .filter_by(status="active", project_id=None, team_id=None)\
                    .order_by(desc(Board.user_order)).first()
            if last_board and last_board.user_order != None:
                new_board.user_order = int(last_board.user_order) + 1
            else: new_board.user_order = 1
        
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
            if current_board.project_id:
                following_boards = Project.query.get(current_board.project_id).boards\
                    .filter(Board.status=="active", Board.project_order>current_board.project_order).all()
                for board in following_boards:
                    board.project_order -=1
            else:
                following_boards = current_user.boards\
                    .filter(Board.status=="active", Board.user_order>current_board.user_order).all()
                for board in following_boards:
                    board.user_order -=1
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
        last_task = Task.query.filter(Task.board_id==id, Task.status!="deleted").order_by(desc(Task.order)).first()
        if not last_task:
            new_task.order = 1
        else:
            new_task.order = last_task.order + 1

        db.session.add(new_task)
        current_user.assigned_tasks.append(new_task)
        for id in dt['assignees']:
            if type(id) is int:
                new_user = User.query.get(id) 
                if new_user:
                    if not new_task in new_user.assigned_tasks:
                        new_user.assigned_tasks.append(new_task)
        
        db.session.commit()
        return jsonify(success=True, task=new_task.as_dict())
    return jsonify(success=False)

@app.route("/board/<id>/gettasks", methods=['GET'])
@login_required
def get_tasks(id):
    current_board = Board(id = id).check_id()
    if not current_board:
        return jsonify(success=False, error=f"There is no board with id#{id}")
    if current_board.tasks:
        current_tasks = current_board.tasks.filter(Task.status != "deleted").order_by(asc(Task.order)).all()
        taskList, tasks = [], {}
        for task in current_tasks:
            tasks[f"task-{task.id}"] = task.as_dict() 
            taskList.append(f"task-{task.id}")
        return jsonify(success=True, tasks=tasks, taskList=taskList)
    return jsonify(success=True, tasks={}, taskList=[] )

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
            elif dt['toggled'] == True:
                current_task.status = "in progress"
            elif dt['toggled'] == False:
                current_task.status = "unfinished"
        if dt['type'] == "edit":
            current_task.body = dt['body'],
            current_task.note = dt['note'],
            current_task.priority = dt['priority'],
            current_task.duedate = datetime.strptime(dt['duedate'], "%Y-%m-%dT%H:%M:%S.%fZ"),
            current_task.assignee_id = dt['assignees'],
        if dt['type'] == "delete":
            current_task.status = dt['status']
            following_tasks = Task.query\
                .filter(Task.status!="deleted", Task.order>current_task.order, Task.board_id==current_task.board_id)\
                    .all()
            if len(following_tasks) > 0:
                for task in following_tasks:
                    task.order -= 1
        db.session.commit()
        return jsonify(success=True, task=current_task.as_dict())    
    return jsonify(success=False)  

# @app.route("/usersuggestion", methods=['GET'])
# @login_required
# def make_suggestions():
    

@app.route("/search", methods=['GET', 'POST'])
@login_required
def search():
    if request.method == "POST":
        dt = request.get_json()
        if dt["query"] != "":
            taskList, results = [], []
            words = dt["query"].split();
            for word in words:
                search = "%{}%".format(word)
                results = Task.query.filter(Task.body.match(search)).filter_by(_or(Task.creator_id==current_user.id, Task.assignee_id==current_user.id)).all()
                print("RESULT", results)
            for task in results:
                taskList.append(f"task#{task.id}: {task.body}")
            return jsonify(success=True, result=taskList)
        
        
    return jsonify(success=False)

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request. %s', e)
    return "An internal error occured", 500