# -*- coding: utf-8 -*-
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

from flask import Blueprint
from flask import flash
from flask import g
from flask import json
from flask import jsonify
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from arxivdigest.frontend.database import general as db
from arxivdigest.frontend.models.errors import ValidationError
from arxivdigest.frontend.models.user import User
from arxivdigest.frontend.models.validate import validPassword
from arxivdigest.frontend.utils import create_gzip_response
from arxivdigest.frontend.utils import encode_auth_token
from arxivdigest.frontend.utils import requiresLogin

mod = Blueprint('general', __name__)


@mod.route('/login', methods=['POST'])
def login():
    """Logs in user based on username and password from form. Returns proper error message on template if
    anything is wrong. Else returns index page and authToken"""
    if g.loggedIn:
        flash('You can\'t login while you\'re already logged in.', 'danger')
        return redirect(url_for('articles.index'))
    data = request.form

    user = db.validatePassword(data.get('email'), data.get('password'))
    if user is None:
        flash('User doesn\'t exist.', 'danger')
        return render_template('login.html')
    if user is False:
        flash('Invalid password.', 'danger')
        return render_template('login.html', )
    next = request.args.get('next', '')
    if next is not '':
        return make_auth_token_response(user, data.get('email'), next)
    return make_auth_token_response(user, data.get('email'),
                                    url_for('articles.index'))


@mod.route('/login', methods=['GET'])
def loginPage():
    """Returns login page or index page if already logged in"""
    if g.loggedIn:
        return redirect(url_for('articles.index'))
    next = request.args.get('next')
    if next:
        err = 'You must be logged in to access this endpoint'
        flash(err, 'danger')
        return render_template('login.html', next=next)
    return render_template('login.html')


@mod.route('/logout', methods=['GET'])
def logout():
    """Returns login page and sets cookie expire time to 0, so that the user gets logged out"""
    resp = make_response(redirect(url_for('general.loginPage')))
    resp.set_cookie('auth', '', expires=0)
    g.user = None
    g.loggedIn = False
    return resp


@mod.route('/signup', methods=['POST'])
def signup():
    """Takes data from signup form and creates an userobject. Sends user object to signup database function. Returns
    signup page with relevant error or index page and authToken"""
    if g.loggedIn:
        flash('You can not register an account while you are already logged in.', 'danger')
        return redirect(url_for('articles.index'))
    form = request.form
    data = form.to_dict()
    try:
        user = User(data)
    except ValidationError as e:
        flash(e.message, 'danger')
        return render_template('signup.html', categoryList=db.getCategoryNames())
    if db.userExist(user.email):
        flash('Email already used by another account.', 'danger')
        return render_template('signup.html', categoryList=db.getCategoryNames())

    id = db.insertUser(user)

    return make_auth_token_response(id, user.email,
                                    url_for('general.signupPage'))


@mod.route('/signup', methods=['GET'])
def signupPage():
    """Returns signup page or index page if already logged in"""
    if g.loggedIn:
        return redirect(url_for('articles.index'))
    return render_template('signup.html', categoryList=db.getCategoryNames())


@mod.route('/passwordChange', methods=['POST'])
@requiresLogin
def passwordChange():
    """Gets old and new password from form. Returns password change template with relevant error
    or profile page on success"""
    data = request.form
    if not data['password'] == data['confirmPassword']:
        flash('Passwords must match.', 'danger')
        return render_template('password_change.html')
    if not validPassword(data['password']):
        flash('New password is invalid', 'danger')
        return render_template('password_change.html')
    if not db.validatePassword(g.email, data['oldPassword']):
        flash('Old password is wrong.', 'danger')
        return render_template('password_change.html')
    db.updatePassword(g.user, data['password'])
    return redirect(url_for('general.profile'))


@mod.route('/passwordChange', methods=['GET'])
@requiresLogin
def passwordChangePage():
    """Returns password change template"""
    return render_template('password_change.html')


@mod.route('/modify', methods=['POST'])
@requiresLogin
def modify():
    """Gets new user data from form. creates user object and sends old user data and new user data to database update
    user function. Returns user modify template with relevant error or user profile template."""
    data = request.form.to_dict()
    try:
        user = User(data, require_password=False)
    except ValidationError as e:
        flash(e.message, 'danger')
        return render_template('modify.html', user=db.get_user(g.user))
    db.update_user(g.user, user)
    return redirect(url_for('general.profile'))


@mod.route('/modify', methods=['GET'])
@requiresLogin
def modifyPage():
    """Returns user modification template with user data filled out"""
    return render_template('modify.html', user=db.get_user(g.user),
                           categoryList=db.getCategoryNames())


@mod.route('/profile', methods=['GET'])
@requiresLogin
def profile():
    """Returns user profile page with user info"""
    return render_template('profile.html', user=db.get_user(g.user))


@mod.route('/livinglab/register', methods=['POST'])
def registerSystem():
    """Registers a system or returns an error if something went wrong."""
    form = request.form.to_dict()
    err, key = db.insertSystem(form['name'], g.user)
    if err:
        flash(err, 'danger')
        return render_template('register_system.html')
    flash('Successfully regstered the system with key: ' + key, 'success')
    return redirect(url_for('general.livinglab'))


@mod.route('/livinglab/register', methods=['GET'])
@requiresLogin
def registerSystemPage():
    """Returns page for registering a new system"""
    return render_template('register_system.html')


@mod.route('/livinglab', methods=['GET'])
def livinglab():
    """Returns page for livinglabs with systems belonging to a user"""
    return render_template('living_lab.html',
                           systems=db.get_user_systems(g.user))


@mod.route('/keyword_feedback/<keyword>/<feedback>', methods=['GET'])
def user_keyword_feedback(keyword, feedback):
    """Endpoint for saving a users feedback on a suggested keyword.
    Returns success or fail"""
    success = db.store_keyword_feedback(g.user, keyword, feedback)
    if success:
        return jsonify(result='success')
    else:
        return jsonify(results='fail')


@mod.route('/feedback/', methods=['GET'])
@requiresLogin
def feedbackPage():
    """Returns feedback page with list of articles."""
    article_id = request.args.get('articleID', '', type=str)
    return render_template('feedback.html', endpoint='general.feedback', article_id=article_id)


@mod.route('/feedback/', methods=['POST'])
def submitFeedback():
    """Submits the feedback form."""
    form = request.form.to_dict()
    try:
        feedback_type = form['feedback_type']
        feedback_text = form['feedback_text']
        if feedback_type in ['Explanation', 'Recommendation']:
            article_id = form['article_id']
        else:
            article_id = None
    except KeyError:
        flash('All fields must be filled in.', 'danger')
        return render_template('feedback.html', endpoint='general.feedback')

    err = db.insertFeedback(g.user, article_id, feedback_type, feedback_text)
    if err:
        flash(err, 'danger')
        return render_template('feedback.html', endpoint='general.feedback')

    flash('Successfully sent feedback.', 'success')
    return redirect('/')


@mod.route('/terms_and_conditions/', methods=['GET'])
def termsandconditions():
    """Returns terms and conditions page."""
    return render_template('terms_and_conditions.html')


@mod.route('/personal_data/', methods=['GET'])
@requiresLogin
def download_personal_data():
    """Returns all the data collected about the currently logged in user.
    :return: gzipped json of user data.
    """
    user_data = db.get_all_userdata(g.user)
    user_data = json.dumps(user_data, sort_keys=True).encode('utf-8')
    return create_gzip_response(user_data, 'arXivDigest_Userdata.json.gz')


def make_auth_token_response(user_id, email, next_page):
    """Creates a Response object that redirects to 'next_page' with
    an authorization token containing the current users info.

    :param user_id: ID of the logged in user.
    :param email: Email of the logged in user.
    :param next_page: Url_path for page to redirect to.
    :return: Response object that redirects to 'next_page', with an auth_token.
    """
    auth_token = encode_auth_token(user_id, email)
    resp = make_response(redirect(next_page))
    resp.set_cookie('auth', auth_token, max_age=60 * 60 * 24 * 10)
    return resp
