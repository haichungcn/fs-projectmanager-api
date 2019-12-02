from flask import flash, redirect
from flask_login import current_user, login_user
from flask_dance.contrib.facebook import make_facebook_blueprint
from flask_dance.consumer import oauth_authorized, oauth_error
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from sqlalchemy.orm.exc import NoResultFound
from .models import db, User, OAuth, Token
import uuid

blueprint = make_facebook_blueprint( 
    storage=SQLAlchemyStorage(OAuth, db.session, user=current_user)
)


# create/login local user on successful OAuth login
@oauth_authorized.connect_via(blueprint) ## /login/facebook/authorized
def facebook_logged_in(blueprint, token):
    if not token:
        flash("Failed to log in.", category="error")
        return False

    resp = blueprint.session.get("/me")
    if not resp.ok:
        msg = "Failed to fetch user info."
        flash(msg, category="error")
        return False

    info = resp.json()
    user_id = info["id"]

    # Find this OAuth token in the database, or create it
    query = OAuth.query.filter_by(provider=blueprint.name, provider_user_id=user_id)
    try:
        oauth = query.one()
    except NoResultFound:
        oauth = OAuth(provider=blueprint.name, provider_user_id=user_id, token=token)

    if oauth.user:
        login_user(oauth.user)
        flash("Successfully signed in.")

    else:
        # Create a new local user account for this user
        user = User(username=info["name"], email=info["name"], password="nonesldjfdf092038402938409823409")
        # Associate the new local user account with the OAuth token
        oauth.user = user
        # Save and commit our database models
        db.session.add_all([user, oauth])
        db.session.commit()
        # Log in the new local user account
        login_user(user)
        flash("Successfully signed in.")

    # Disable Flask-Dance's default behavior for saving the OAuth token
    #redirect to font end with token
    token_query = Token.query.filter_by(user_id=current_user.id)
    try:
        token = token_query.one()
    except NoResultFound:
        token = Token(user_id=current_user.id, uuid=str(uuid.uuid4().hex))
        db.session.add(token)
        db.session.commit()
    # return redirect("https://xenodochial-mahavira-452f56.netlify.com/?api_key={}".format(token.uuid))
    return redirect("https://127.0.0.1:3000/?api_key={}".format(token.uuid))


# notify on OAuth provider error
@oauth_error.connect_via(blueprint)
def facebook_error(blueprint, message, response):
    msg = ("OAuth error from {name}! " "message={message} response={response}").format(
        name=blueprint.name, message=message, response=response
    )
    flash(msg, category="error")
