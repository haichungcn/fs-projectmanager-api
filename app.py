from flask import Flask, jsonify, request
from flask_login import UserMixin, login_user, logout_user, login_required, current_user
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
CORS(app)

app.secret_key = 'Huper hecret'
app.config['SQLALCHEMY_DATABASE_URI']='postgresql://haict:password@localhost:5432/typeracer'

db = SQLAlchemy(app)

migrate = Migrate(app, db)

class User(UserMixin,db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), nullable=False, unique=True)
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.Text, nullable=False)
    scores = db.relationship('Score', backref='user')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def check_email(self):
        return User.query.filter_by(email=self.email).first()

class Score(db.Model):
    __tablename__ = 'scores'
    id = db.Column(db.Integer, primary_key=True)
    wpm = db.Column(db.Float, nullable=False)
    time = db.Column(db.Integer, nullable=False)
    accuracy = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    excerpt_id = db.Column(db.Integer, db.ForeignKey('excerpts.id'))

    def as_dict(self):
        return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}


class Excerpt(db.Model):
    __tablename__ = 'excerpts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    scores = db.relationship('Score', backref='excerpt', lazy=True)
    
    def as_dict(self):
        return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}


@app.route('/', methods=['GET'])
def root():
    return jsonify(['Hello', 'World'])

@app.route('/user/id', methods=['GET'])
def user():
    excerpts = Excerpt.query.all()
    jsonized_excerpt_objects_list = []
    for excerpt in excerpts:
        jsonized_excerpt_objects_list.append(excerpt.as_dict())

    return jsonify(jsonized_excerpt_objects_list)

@app.route('/excerpts', methods=['GET'])
def excerpts():
    excerpts = Excerpt.query.all()
    jsonized_excerpt_objects_list = []
    for excerpt in excerpts:
        jsonized_excerpt_objects_list.append(excerpt.as_dict())

    return jsonify(jsonized_excerpt_objects_list)

@app.route('/scores', methods=['GET', 'POST'])
def create_score():
    # import code; code.interact(local=dict(globals().**locals()))
    if request.method == 'POST':
        dt = request.get_json()
        score = Score(
            time = dt['time'],
            wpm = dt['wpm'],
            accuracy = dt['errorCount'],
            excerpt_id = dt['excerpt_id'],
            user_id = dt['user_id']
            )
        db.session.add(score)
        db.session.commit()
        excerpt = Excerpt.query.get(dt[('excerpt_id')])
        scores = Score.query.filter_by(excerpt_id=dt[('excerpt_id')]).order_by(Score.wpm.desc()).limit(3)
        count = Score.query.filter_by(excerpt_id=dt[('excerpt_id')]).count()
        response = {
            'id': excerpt.id,
            'text': excerpt.body,
            'user_score': count,
            'scores': {
                'top': [{'id': score.id, 'value': score.wpm} for scrore in scores],
                'count': count,
            }
        }
        return jsonify(response)
        
@app.route('/highscores', methods=['GET', 'POST'])
def get_high_score():
    # import code; code.interact(local=dict(globals().**locals()))
    if request.args.get('filter') == 'all':
        scores = Score.query.order_by(Score.wpm.desc()).limit(3)
        count = Score.query.order_by(Score.wpm.desc()).count()
        response = {
            'top': [{'id': score.id, 'value': score.wpm, 'time': score.time, 'accuracy': score.accuracy} for scrore in scores],
            'count': count,
        }
    # if reqest.args.get('filter') == 'excerpt':
        # dt = request.get_json()
        # score = Score(
        #     time = dt['time'],
        #     wpm = dt['wpm'],
        #     accuracy = dt['errorCount'],
        #     excerpt_id = dt['excerpt_id'],
        #     user_id = dt['user_id']
        #     )
        # db.session.add(score)
        # db.session.commit()
        # excerpt = Excerpt.query.get(dt[('excerpt_id')])
        # scores = Scores.query.filter_by(excerpt_id=dt[('excerpt_id')]).order_by(Score.wpm.desc()).limit(3)
        # count = Scores.query.filter_by(excerpt_id=dt[('excerpt_id')]).count()
        # response = {
        #     'id': excerpt.id,
        #     'text': excerpt.body,
        #     'user_score': count,
        #     'scores': {
        #         'top': [{'id': score.id, 'value': score.wpm} for scrore in scores],
        #         'count': count,
        #     }
        # }
    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True, ssl_context='adhoc')

