from flask import Flask, redirect, url_for, flash, render_template, jsonify, request
from flask_login import login_required, logout_user, current_user
from .config import Config
from .models import db, login_manager, Token, User, Excerpt, Score
from .oauth import blueprint
from .cli import create_db
from flask_migrate import Migrate
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)


app.register_blueprint(blueprint, url_prefix="/login")


app.cli.add_command(create_db)
db.init_app(app)

migrate = Migrate(app, db)
login_manager.init_app(app)


@app.route("/")
def index():
    return render_template("home.html")

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
    if token:
        db.session.delete(token)
        db.session.commit()
    logout_user()
    flash("You have logged out")
    return jsonify({
        "success":True
    })


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
        print(dt)
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