from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin

from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


db = SQLAlchemy()


class User(UserMixin,db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200))
    email_confirmed_at = db.Column(db.DateTime(timezone=True))
    username = db.Column(db.String(200))
    password = db.Column(db.Text)
    status = db.Column(db.String, default='unfinished')
    avatar_url = db.Column(db.Text)
    origin = db.Column(db.String(200))
    boardOrder = db.Column(db.String)
    timestamp = db.Column(db.DateTime(timezone=True), server_default = db.func.now())

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    assigned_tasks = db.relationship('Task', foreign_keys='Task.assignee_id', backref=db.backref('assigned_user', lazy=True))
    created_tasks = db.relationship('Task', foreign_keys='Task.creator_id', backref=db.backref('creator', lazy=True))
    boards = db.relationship('Board', backref=db.backref('user', lazy=True), lazy='dynamic')
    teams = db.relationship('Team', secondary='team_users', backref=db.backref('users', lazy=True))
    projects = db.relationship('Project', secondary='user_projects', backref=db.backref('users', lazy=True))

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def check_email(self):
        return User.query.filter_by(email=self.email).first()

    def as_dict(self):
        return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}
        
# Define the Role data-model
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)
    users = db.relationship('User', backref=db.backref('role'))

class OAuth(OAuthConsumerMixin, db.Model):
    provider_user_id = db.Column(db.String(256), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship(User)

class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String, unique=True) #token
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship(User)
    timestamp = db.Column(db.DateTime(timezone=True), server_default = db.func.now())

class Board(db.Model):
    __tablename__ = 'boards'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    status = db.Column(db.String, default="active")
    tasks = db.relationship("Task", backref="board", lazy='dynamic')
    timestamp = db.Column(db.DateTime(timezone=True), server_default = db.func.now())
    parent_id = db.Column(db.Integer)

    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user_order = db.Column(db.Integer)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    project_order = db.Column(db.Integer)

    def check_id(self):
        return Board.query.filter_by(id=self.id).first()

    def delete_all(self):
        all_tasks = Board.query.filter_by(id=self.id).first().tasks.all()
        if len(all_tasks) < 1:
            return False
        for task in all_tasks:
            task.status = "deleted"
        return True

    def as_dict(self):
        return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String)
    note = db.Column(db.Text)
    status = db.Column(db.String, default='unfinished')
    priority = db.Column(db.Integer, default=1)
    parent_id = db.Column(db.Integer, default=0)
    board_id = db.Column(db.Integer, db.ForeignKey('boards.id'))
    order = db.Column(db.Integer)
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    duedate = db.Column(db.DateTime(timezone=True))
    timestamp = db.Column(db.DateTime(timezone=True), server_default = db.func.now())

    def check_id(self):
        return Task.query.filter_by(id=self.id).first()
    
    def as_dict(self):
        return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}

class Team(db.Model):
    __tablename__ = 'teams'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    status = db.Column(db.String, default="active")
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    boards = db.relationship('Board', backref=db.backref('team', lazy=True), lazy='dynamic')
    boardOrder = db.Column(db.String)
    projects = db.relationship('Project', backref=db.backref('teams', lazy=True), lazy="dynamic")
    timestamp = db.Column(db.DateTime(timezone=True), server_default = db.func.now())
    
    def as_dict(self):
        return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}
    def delete_all(self):
        projects = Team.query.get(id).projects.all()
        for project in projects:
            project.status = "deleted"
            project.delete_all()

class Teamuser(db.Model):
    __tablename__ = 'team_users'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), primary_key=True)
    role = db.Column(db.String, default='member')


class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    status = db.Column(db.String, default="active")
    project_type = db.Column(db.String)
    boards = db.relationship('Board', backref=db.backref('project', lazy=True), lazy='dynamic')
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    timestamp = db.Column(db.DateTime(timezone=True), server_default = db.func.now())

    def as_dict(self):
        return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}
    def delete_all(self):
        boards = Project.query.get(id).boards.all()
        for board in boards:
            board.status = "deleted"
            board.delete_all()


user_projects = db.Table('user_projects',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('project_id', db.Integer, db.ForeignKey('projects.id'))
)

# setup login manager
login_manager = LoginManager()
# login_manager.login_view = "facebook.login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.request_loader
def load_user_from_request(request):
    api_key = request.headers.get('Authorization')
    # print('request authorization:', api_key)
    if api_key:
        api_key = api_key.replace('Token ', '', 1)
        token = Token.query.filter_by(uuid=api_key).first()
        current_datetime = datetime.now().astimezone(tz=None)
        if token:
            # print('comparing token timestamp:', token.timestamp, 'and current_datetime: ', current_datetime, 'is token > current_datetime', token.timestamp > current_datetime)
            # print('token matched', token, token.user)
            return token.user
    return None