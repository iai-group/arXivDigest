# -*- coding: utf-8 -*-
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2018, The ArXivDigest Project'

from flask import Blueprint, request, make_response, g, jsonify, render_template, redirect, flash, url_for
from frontend.models.user import User
from frontend.models.system import System
from frontend.models.validate import validPassword
from frontend.models.errors import ValidationError
from frontend.database import general as db
from frontend.utils import encode_auth_token, requiresLogin
from frontend.scrape_keywords.find_titles import find_author_titles

mod = Blueprint('general', __name__)


@mod.route('/login', methods=['POST'])
def login():
    '''Logs in user based on username and password from form. Returns proper error message on template if 
    anything is wrong. Else returns index page and authToken'''
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
        return makeAuthTokenResponse(user, data.get('email'), next)
    return makeAuthTokenResponse(user, data.get('email'), url_for('articles.index'))


@mod.route('/login', methods=['GET'])
def loginPage():
    '''Returns login page or index page if already logged in'''
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
    '''Returns login page and sets cookie expire time to 0, so that the user gets logged out'''
    resp = make_response(redirect(url_for('general.loginPage')))
    resp.set_cookie('auth', '', expires=0)
    g.user = None
    g.loggedIn = False
    return resp


@mod.route('/signup', methods=['POST'])
def signup():
    '''Takes data from signup form and creates an userobject. Sends user object to signup database function. Returns
    signup page with relevant error or index page and authToken'''
    if g.loggedIn:
        flash('You can not register an account while you are already logged in.', 'danger')
        return redirect(url_for('articles.index'))
    form = request.form
    data = form.to_dict()
    data['website'] = form.getlist('website')
    try:
        user = User(data)
    except ValidationError as e:
        flash(e.message, 'danger')
        return render_template('signup.html', categoryList=db.getCategoryNames())
    if db.userExist(user.email):
        flash('Email already used by another account.', 'danger')
        return render_template('signup.html', categoryList=db.getCategoryNames())

    id = db.insertUser(user)

    return makeAuthTokenResponse(id, user.email, url_for('general.signupPage'))


@mod.route('/signup', methods=['GET'])
def signupPage():
    '''Returns signup page or index page if already logged in'''
    if g.loggedIn:
        return redirect(url_for('articles.index'))
    return render_template('signup.html', categoryList=db.getCategoryNames())


@mod.route('/passwordChange', methods=['POST'])
@requiresLogin
def passwordChange():
    '''Gets old and new password from form. Returns password change template with relevant error 
    or profile page on success'''
    data = request.form
    if not data['password'] == data['confirmPassword']:
        flash('Passwords must match.', 'danger')
        return render_template('passwordChange.html')
    if not validPassword(data['password']):
        flash('New password is invalid', 'danger')
        return render_template('passwordChange.html')
    if not db.validatePassword(g.email, data['oldPassword']):
        flash('Old password is wrong.', 'danger')
        return render_template('passwordChange.html')
    db.updatePassword(g.user, data['password'])
    return redirect(url_for('general.profile'))


@mod.route('/passwordChange', methods=['GET'])
@requiresLogin
def passwordChangePage():
    '''Returns password change template'''
    return render_template('passwordChange.html')


@mod.route('/modify', methods=['POST'])
@requiresLogin
def modify():
    '''Gets new user data from form. creates user object and sends old user data and new user data to database update
    user function. Returns user modify template with relevant error or user profile template.'''
    form = request.form
    data = form.to_dict()
    data['website'] = form.getlist('website')
    # just to get through user object creation, is not used
    data['password'] = 'ASD!"#asd123'
    try:
        user = User(data)
    except ValidationError as e:
        flash(e.message, 'danger')
        return render_template('modify.html', user=db.getUser(g.user))
    db.updateUser(g.user, user)
    return redirect(url_for('general.profile'))


@mod.route('/modify', methods=['GET'])
@requiresLogin
def modifyPage():
    '''Returns user modification template with user data filled out'''
    user = db.getUser(g.user)
    return render_template('modify.html', user=user, categoryList=db.getCategoryNames())


@mod.route('/profile', methods=['GET'])
@requiresLogin
def profile():
    '''Returns user profile page with user info'''
    user = db.getUser(g.user)
    return render_template('profile.html', user=user)


@mod.route('/system/register', methods=['POST'])
def registerSystem():
    '''Registers a system or returns an error if something went wrong.'''
    form = request.form.to_dict()
    try:
        system = System(form)
    except ValidationError as e:
        flash(e.message, 'danger')
        return render_template('registerSystem.html')
    err = db.insertSystem(system)
    if err:
        flash(err, 'danger')
        return render_template('registerSystem.html')
    flash('Successfully sent the system registration.', 'success')
    return render_template('registerSystem.html')


@mod.route('/system/register', methods=['GET'])
def registerSystemPage():
    '''Returns page for registering a new system'''
    return render_template('registerSystem.html')

@mod.route('/author_keywords/<path:author_url>', methods=['GET'])
def author_keywords(author_url):
    '''Endpoint for fetching an authors keywords from their dblp article url.
    Returns list of keywords or an empty string for failure.'''
    author_titles = find_author_titles(author_url) 
    if author_titles == "":
        return jsonify(keywords="")
    keywords = db.get_keywords_from_titles(author_titles, 30, g.user)
    if len(keywords) > 0:
        return jsonify(keywords=keywords)
    return jsonify(keywords="")

@mod.route('/keyword_opinion/<keyword>/<opinion>', methods=['GET'])
def send_user_opinion(keyword, opinion):
    """Endpoint for saving a users opinion on a suggested keyword.
    Returns success or fail"""
    result = db.store_keyword_opinion(g.user, keyword, opinion)
    if result:
        return jsonify(result="success")
    else:
        return jsonify(results="fail")

def makeAuthTokenResponse(id, email, next):
    '''creates an authToken for a user with id and email. Then redirects to next'''
    authToken = encode_auth_token(id, email)
    resp = make_response(redirect(next))
    resp.set_cookie('auth', authToken, max_age=60 * 60 * 24 * 10)
    return resp
