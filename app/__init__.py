from flask import Flask, redirect, url_for, flash, render_template, jsonify, request
from flask_login import login_required, logout_user, current_user
from .config import Config
from .models import db, login_manager, Token, User
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