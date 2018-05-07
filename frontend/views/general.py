__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"

from flask import Blueprint, request, make_response, g, jsonify, render_template, redirect

from frontend.models.user import User
from frontend.models.errors import ValidationError
from frontend.database import general as db
from frontend.utils import encode_auth_token, requiresLogin

mod = Blueprint('general', __name__)


@mod.route('/login', methods=['POST'])
def login():
    '''Logs in user based on username and password from form. Returns proper error message on template if 
    anything is wrong. Else returns index page and authToken'''
    if g.loggedIn:
        return make_response(jsonify({'err': 'You can\'t register an account while you\'re already logged in.'})), 400
    data = request.form

    user = db.validatePassword(data.get('email'), data.get('password'))
    if user is None:
        return render_template('login.html', err='User doesn\'t exist.')
    if user is False:
        return render_template('login.html', err='Invalid password.')
    next = request.args.get("next", "")
    if next is not "":
        return makeAuthTokenResponse(user, data.get('email'), next)
    return makeAuthTokenResponse(user, data.get('email'), '/')


@mod.route('/login', methods=['GET'])
def loginPage():
    '''Returns login page or index page if already logged in'''
    if g.loggedIn:
        return redirect('/')
    next = request.args.get("next")
    if next:
        err = 'You must be logged in to access this endpoint'
        return render_template('login.html', err=err, next=next)
    return render_template('login.html')


@mod.route('/logout', methods=['GET'])
def logout():
    '''Returns login page and sets cookie expire time to 0, so that the user gets logged out'''
    resp = make_response(redirect('/login'))
    resp.set_cookie('auth', '', expires=0)
    g.user = None
    g.loggedIn = False
    return resp


@mod.route('/signup', methods=['POST'])
def signup():
    '''Takes data from signup form and creates an userobject. Sends user object to signup database function. Returns
    signup page with relevant error or index page and authToken'''
    if g.loggedIn:
        return make_response(jsonify({'err': 'You can not register an account while you are already logged in.'})), 400
    form = request.form
    data = form.to_dict()
    data['website'] = form.getlist('website')
    try:
        user = User(data)
    except ValidationError as e:
        return render_template('signup.html', err=e.message)
    if db.userExist(user.email):
        return render_template('signup.html', err='Email already used by another account.')

    id = db.insertUser(user)

    return makeAuthTokenResponse(id, user.email, '/')


@mod.route('/signup', methods=['GET'])
def signupPage():
    '''Returns signup page or index page if already logged in'''
    if g.loggedIn:
        return redirect('/')
    return render_template('signup.html', categoryList=db.getCategoryNames())


@mod.route('/passwordChange', methods=['POST'])
@requiresLogin
def passwordChange():
    '''Gets old and new password from form. Returns password change template with relevant error 
    or profile page on success'''
    data = request.form
    if not data['password'] == data['confirmPassword']:
        return render_template('passwordChange.html', err='Passwords must match.')
    if not User.validPassword(data['password']):
        return render_template('passwordChange.html', err='New password is invalid')
    if not db.validatePassword(g.email, data['oldPassword']):
        return render_template('passwordChange.html', err='Old password is wrong.')
    db.updatePassword(g.user, data['password'])
    return render_template('profile.html', user=db.getUser(g.user))


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
        return render_template('modify.html', user=db.getUser(g.user), err=e.message)
    db.updateUser(g.user, user)
    return render_template('profile.html', user=db.getUser(g.user))


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


def makeAuthTokenResponse(id, email, next):
    '''creates an authToken for a user with id and email. Then redirects to next'''
    authToken = encode_auth_token(id, email)
    resp = make_response(redirect(next))
    resp.set_cookie('auth', authToken, max_age=60 * 60 * 24 * 10)
    return resp
