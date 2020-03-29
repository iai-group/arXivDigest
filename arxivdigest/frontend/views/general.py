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

from arxivdigest.core.config import CONSTANTS
from arxivdigest.frontend.database import general as db
from arxivdigest.frontend.database.articles import article_is_recommended_for_user
from arxivdigest.frontend.database.articles import get_article_feedback
from arxivdigest.frontend.forms.feedback_form import ArticleFeedbackForm
from arxivdigest.frontend.forms.feedback_form import FeedbackForm
from arxivdigest.frontend.models.errors import ValidationError
from arxivdigest.frontend.models.user import User
from arxivdigest.frontend.models.validate import validPassword
from arxivdigest.frontend.utils import create_gzip_response
from arxivdigest.frontend.utils import encode_auth_token
from arxivdigest.frontend.utils import requiresLogin
from arxivdigest.frontend.utils import send_confirmation_email

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
    if g.loggedIn and not g.inactive:
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
    signup page with relevant error or confirm email page and authToken"""
    if g.loggedIn:
        flash('You can not sign up while you are already logged in.', 'danger')
        return redirect(url_for('articles.index'))
    user_dict = request.form.to_dict()
    try:
        user = User(user_dict)
    except ValidationError as e:
        flash(e.message, 'danger')
        return render_template('signup.html', user=user_dict, signup=True,
                               categoryList=db.getCategoryNames())
    if db.userExist(user.email):
        flash('Email already used by another account.', 'danger')
        return render_template('signup.html', user=user_dict, signup=True,
                               categoryList=db.getCategoryNames())

    id = db.insertUser(user)

    send_confirmation_email(user.email)
    return make_auth_token_response(id, user.email,
                                    url_for('general.confirm_email_page'))


@mod.route('/signup', methods=['GET'])
def signupPage():
    """Returns signup page or index page if already logged in"""
    if g.loggedIn:
        return redirect(url_for('articles.index'))
    return render_template('signup.html', signup=True,
                           categoryList=db.getCategoryNames())


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
    user_dict = request.form.to_dict()
    try:
        user = User(user_dict, require_password=False)
    except ValidationError as e:
        flash(e.message, 'danger')
        return render_template('modify.html', user=user_dict,
                               categoryList=db.getCategoryNames())
    if db.userExist(user.email):
        flash('Email already used by another account.', 'danger')
        return render_template('modify.html', user=user_dict,
                               categoryList=db.getCategoryNames())

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
@requiresLogin
def registerSystem():
    """Registers a system or returns an error if something went wrong."""
    form = request.form.to_dict()
    if len(form['name']) > CONSTANTS.max_system_name_length:
        flash('System name must be under {} characters.'.format(
            CONSTANTS.max_system_name_length), 'danger')
        return render_template('register_system.html')
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
@requiresLogin
def livinglab():
    """Returns page for livinglabs with systems belonging to a user"""
    return render_template('living_lab.html',
                           systems=db.get_user_systems(g.user),
                           user=db.get_user(g.user))


@mod.route('/feedback/', methods=['GET', 'POST'])
def feedback():
    """Endpoint for general feedback."""
    form = FeedbackForm()
    if form.validate_on_submit():
        err = db.insertFeedback(g.user, None, form.feedback_type.data,
                                form.feedback_text.data, {})
        if err:
            flash(err, 'danger')
            return render_template('feedback.html', form=form)

        flash('Successfully sent feedback.', 'success')
        return redirect('/')

    return render_template('feedback.html', form=form)


@mod.route('/feedback/articles/<article_id>', methods=['GET', 'POST'])
@requiresLogin
def article_feedback(article_id):
    """Submits the feedback form."""
    form = ArticleFeedbackForm()
    if not article_is_recommended_for_user(article_id):
        flash('You can only leave feedback on articles recommended to you.',
              'danger')
        return redirect('/')

    if form.validate_on_submit():
        feedback_vals = {}
        if form.relevance.data is not None:
            feedback_vals['relevance'] = form.relevance.data
        if form.expl_satisfaction.data is not None:
            feedback_vals['expl_satisfaction'] = form.expl_satisfaction.data
        if form.expl_persuasiveness.data is not None:
            feedback_vals['expl_persuasiveness'] = form.expl_persuasiveness.data
        if form.expl_transparency.data is not None:
            feedback_vals['expl_transparency'] = form.expl_transparency.data
        if form.expl_scrutability.data is not None:
            feedback_vals['expl_scrutability'] = form.expl_scrutability.data

        err = db.insertFeedback(g.user, article_id, form.feedback_type.data,
                                form.feedback_text.data, feedback_vals)
        if err:
            flash(err, 'danger')
            return render_template('feedback.html', form=form,
                                   article_id=article_id)

        flash('Successfully sent feedback.', 'success')
        return redirect('/')
    return render_template('feedback.html', form=form,
                           article=get_article_feedback(article_id))


@mod.route('/about/', methods=['GET'])
def about():
    """Returns about page."""
    return render_template('about.html')


@mod.route('/terms_and_conditions/', methods=['GET'])
def terms_and_conditions():
    """Returns terms and conditions page."""
    return render_template('terms_and_conditions.html')


@mod.route('/privacy_policy/', methods=['GET'])
def privacy_policy():
    """Returns privacy policy page."""
    return render_template('privacy_policy.html')


@mod.route('/topics/search/<search_string>', methods=['GET'])
def topic_search(search_string):
    """Returns a json containing topics starting with ´search_string´."""
    return jsonify(db.search_topics(search_string))


@mod.route('/personal_data/', methods=['GET'])
@requiresLogin
def download_personal_data():
    """Returns all the data collected about the currently logged in user.
    :return: gzipped json of user data.
    """
    user_data = db.get_all_userdata(g.user)
    user_data = json.dumps(user_data, sort_keys=True).encode('utf-8')
    return create_gzip_response(user_data, 'arXivDigest_Userdata.json.gz')

@mod.route('/update_topic/<topic_id>/<state>', methods=['GET'])
@requiresLogin
def update_topic(topic_id, state):
    """Updates the state of the topics to system approved or rejected."""
    if not db.update_user_topic(topic_id, g.user, state):
        return jsonify(result='fail')
    return jsonify(result='success')

@mod.route('/refresh_topics', methods=['GET'])
@requiresLogin
def refresh_topics():
    """Refreshe the list of topics on the index page and returns list
    of new topics."""
    db.clear_suggested_user_topics(g.user,'REFRESHED')
    return jsonify(result = db.get_user_topics(g.user))
    

@mod.route('/confirm_email', methods=['GET'])
def confirm_email_page():
    """Returns page for users that have not confirmed their 
    email address"""
    if not g.loggedIn:
        return redirect(url_for('general.loginPage'))
    if not g.inactive:
        return redirect(url_for('articles.index'))
    next = request.args.get('next')
    if next:
        err = 'You must confirm your email to access this endpoint'
        flash(err, 'danger')
        return render_template('confirm_email.html', next=next, email=g.email)
    return render_template('confirm_email.html', email=g.email)

@mod.route('/send_email', methods=['POST'])
def send_email():
    """Updates the user with email from form and sends new email."""
    if not g.loggedIn:
        return redirect(url_for('general.loginPage'))

    email = request.form.to_dict()['email']
    if db.userExist(email):
        flash('Email is already in use.', 'danger')
        return redirect(url_for('general.confirm_email_page'))
    db.update_email(email, g.user)
    send_confirmation_email(email)
    flash('New email has been sent.', 'success')
    return make_auth_token_response(g.user, email,
                                    url_for('general.confirm_email_page'))


@mod.route('/email_confirm/<uuid:trace>', methods=['GET'])
def activate_user(trace):
    """Activates a user. Returns index if logged in, loginpage if not."""
    if not db.activate_user(str(trace)):
        flash('Invalid activation link.', 'danger')
        return redirect(url_for('general.confirm_email_page'))
    if g.loggedIn:
        return make_auth_token_response(g.user, g.email,
                                        url_for('articles.index'))
    else:
        return redirect(url_for('general.loginPage'))

@mod.route('/mail/unsubscribe/<uuid:trace>', methods=['GET'])
def unsubscribe(trace):
    if not db.digest_unsubscribe(str(trace)):
        flash('Invalid unsubscribe link.', 'danger')
        return redirect(url_for('articles.index'))
    return render_template('unsubscribed.html')

def make_auth_token_response(user_id, email, next_page):
    """Creates a Response object that redirects to 'next_page' with
    an authorization token containing the current users info.

    :param user_id: ID of the logged in user.
    :param email: Email of the logged in user.
    :param next_page: Url_path for page to redirect to.
    :return: Response object that redirects to 'next_page', with an auth_token.
    """
    auth_token = encode_auth_token(user_id, email)
    resp = redirect(next_page)
    resp.set_cookie('auth', auth_token, max_age=60 * 60 * 24 * 10)
    return resp
