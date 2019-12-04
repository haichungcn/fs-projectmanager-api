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
    avatar_url = db.Column(db.Text)
    origin = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime(timezone=True), server_default = db.func.now())

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    tasks = db.relationship('Task', backref=db.backref('user', lazy=True))
    boards = db.relationship('Board', backref=db.backref('user', lazy=True))
    teams = db.relationship('Team', secondary='team_users', backref=db.backref('users', lazy=True))
    projects = db.relationship('Project', secondary='user_projects', backref=db.backref('users', lazy=True))

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def check_email(self):
        return User.query.filter_by(email=self.email).first()

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
    tasks = db.relationship("Task", backref="board")
    timestamp = db.Column(db.DateTime(timezone=True), server_default = db.func.now())

    leader_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    board_id = db.Column(db.Integer, db.ForeignKey('boards.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime(timezone=True), server_default = db.func.now())

class Team(db.Model):
    __tablename__ = 'teams'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))

team_users = db.Table('team_users',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('team_id', db.Integer, db.ForeignKey('teams.id'))
)

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))

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
    if api_key:
        api_key = api_key.replace('Token ', '', 1)
        token = Token.query.filter_by(uuid=api_key).first()
        current_datetime = datetime.now()
        if token:
            print('comparing token timestamp:', token.timestamp, 'and current_datetime: ', current_datetime)
            return token.user
    return None