# -*- coding: utf-8 -*-

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

from datetime import datetime

from flask import Flask
from flask import g
from flask import jsonify
from flask import make_response
from flask import request

import arxivdigest.api.database as db
import arxivdigest.api.validator as validation
from arxivdigest.api.utils import CustomJSONEncoder, CustomJSONProvider
from arxivdigest.api.utils import getUserlist
from arxivdigest.api.utils import validateApiKey
from arxivdigest.core.config import config_api

from arxivdigest.core.config import CONSTANTS

app = Flask(__name__)

@app.before_request
def before_request():
    """Check JWT auth tokens for user endpoints"""
    import jwt
    from arxivdigest.core.config import jwtKey
    
    # Skip auth for OPTIONS and public endpoints
    if request.method == 'OPTIONS' or request.endpoint == 'info':
        return
    
    # Handle JWT authentication for user endpoints
    user_endpoints = ['login', 'signup', 'profile', 'modify', 'logout', 'user_topics', 'user_categories', 'user_recommendations', 'user_saved', 'save_article', 'password_change', 'download_user_data', 'user_systems', 'system_statistics', 'system_feedback', 'register_system', 'admin_general', 'admin_systems', 'admin_toggle_system', 'admin_admins']
    if request.endpoint in user_endpoints:
        authToken = request.cookies.get("auth")
        try:
            if authToken and isinstance(authToken, bytes):
                authToken = authToken.decode('utf-8')
            
            if authToken:
                payload = jwt.decode(authToken, jwtKey, algorithms=["HS256"])
                g.user = int(payload.get('sub', None))
                g.email = payload.get('email', None)
                g.admin = payload.get('admin', False)
                g.inactive = payload.get('inactive', True)
                g.loggedIn = True
            else:
                g.user = None
                g.email = None
                g.admin = False
                g.loggedIn = False
                g.inactive = True
        except Exception:
            g.user = None
            g.email = None
            g.admin = False
            g.loggedIn = False
            g.inactive = True

@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    # Allow all localhost origins for development
    if origin and ('localhost' in origin or '127.0.0.1' in origin):
        response.headers['Access-Control-Allow-Origin'] = origin
    else:
        response.headers['Access-Control-Allow-Origin'] = '*'
    
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-Requested-With'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Max-Age'] = '86400'
    return response

@app.route('/<path:path>', methods=['OPTIONS'])
@app.route('/', methods=['OPTIONS'])
def handle_options(path=None):
    response = make_response('', 200)
    return response

app.config.update(**config_api)
# Use modern JSON provider for Flask 2.2+
app.json_provider_class = CustomJSONProvider


@app.route('/user_feedback/articles', methods=['GET'])
@validateApiKey
@getUserlist
def user_feedback_articles(users):
    """API-endpoint for requesting user_feedback for articles, 'user_id' must be
    one or more ids separated by comma."""
    return jsonify(db.get_user_feedback_articles(users))


@app.route('/user_feedback/topics', methods=['GET'])
@validateApiKey
@getUserlist
def user_feedback_topics(users):
    """API-endpoint for requesting user feedback for topics, 'user_id' must be
    one or more ids separated by comma."""
    return jsonify(db.get_user_feedback_topics(users))


@app.route('/users', methods=['GET'])
@validateApiKey
def users():
    """API-endpoint for fetching userIDs, ids will be returned in batches
    starting from 'fromID'.
    If 'fromID' is unspecified 0 will be used as default."""
    try:
        fromID = int(request.args.get('from', 0))
        if fromID < 0:
            return make_response(jsonify({'error': '"from" must be positive'}), 400)
    except Exception:
        err = '"from" must be an integer'
        return make_response(jsonify({'error': err}), 400)

    users = db.getUserIDs(fromID, app.config['max_userid_request'])
    return make_response(jsonify({'users': users}), 200)


@app.route('/user_info', methods=['GET'])
@validateApiKey
@getUserlist
def user_info(users):
    """API-endpoint for requesting userdata, 'user_id' must be one or more ids
    separated by comma."""
    return make_response(jsonify({'user_info': db.getUsers(users)}), 200)


@app.route('/articles', methods=['GET'])
@validateApiKey
def articles():
    """API-endpoint for requesting articleIDs of articles from the last 7
    days."""
    return make_response(jsonify({
        'articles': db.get_article_ids_past_seven_days()}), 200)


@app.route('/article_data', methods=['GET'])
@validateApiKey
def article_data():
    """API-endpoint for requesting article_data, 'article_id' must be one or
    more ids separated by comma."""
    try:
        ids = request.args.get('article_id').split(',')
    except Exception:
        return make_response(jsonify({'error': 'No IDs supplied.'}, 400))
    if (len(ids) > app.config['max_articledata_request']):
        err = 'You cannot request more than %s articles at a time.' % app.config[
            'max_articledata_request']
        return make_response(jsonify({'error': err}), 400)

    articles = db.checkArticlesExists(ids)
    if len(articles) > 0:
        err = 'Could not find articles with ids: %s.' % ', '.join(articles)
        return make_response(jsonify({'error': err}), 400)

    articles = db.get_article_data(ids)
    return make_response(jsonify({'articles': articles}), 200)

@app.route('/topics', methods=['GET'])
@validateApiKey
def topics():
    """API-endpoint for requesting a list of all topics currently
    stored in arXivDigest."""
    topics = db.get_topics()
    return make_response(jsonify({'topics': topics}), 200)

@app.route('/recommendations/articles', methods=['POST'])
@validateApiKey
@validation.validate_json(validation.article_recommendation)
def make_article_recommendations():
    """API-endpoint for inserting article recommendations"""
    data = request.get_json().get('recommendations')
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    data = [(k, v['article_id'], g.sysID, v['explanation'], v['score'], now)
            for k, v in data.items() for v in v]

    db.insert_article_recommendations(data)
    return make_response(jsonify({'success': True}), 200)


@app.route('/recommendations/topics', methods=['POST'])
@validateApiKey
@validation.validate_json(validation.topic_recommendation)
def make_topic_recommendations():
    """API-endpoint for inserting topic recommendations"""
    json = request.get_json().get('recommendations')

    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    data = []
    for user, recommendations in json.items():
        for recommendation in recommendations:
            data.append({'user_id': user,
                         'topic': recommendation['topic'],
                         'system_id': g.sysID,
                         'date': now,
                         'score': recommendation['score']})

    db.insert_topic_recommendations(data)
    return make_response(jsonify({'success': True}), 200)


@app.route('/recommendations/articles', methods=['GET'])
@validateApiKey
@getUserlist
def get_article_recommendations(users):
    """API-endpoint for requesting user-recommendations of articles,
     "user_id" must be one or more ids separated by comma."""
    users = db.get_article_recommendations(users)
    return make_response(jsonify({'users': users}), 200)


@app.route('/recommendations/topics', methods=['GET'])
@validateApiKey
@getUserlist
def get_topic_recommendations(users):
    """API-endpoint for requesting user-recommendations of topics,
     "user_id" must be one or more ids separated by comma."""
    topic_recommendations = db.get_topic_recommendations(users)
    return make_response(jsonify({'users': topic_recommendations}), 200)


@app.route('/login', methods=['POST'])
def login():
    """API endpoint for user login"""
    from arxivdigest.frontend.database import general as frontend_db
    from arxivdigest.frontend.utils import encode_auth_token
    
    data = request.form
    user = frontend_db.validatePassword(data.get("email"), data.get("password"))
    
    if user is None:
        return make_response(jsonify({'error': 'User does not exist'}), 401)
    if user is False:
        return make_response(jsonify({'error': 'Invalid password'}), 401)
    
    auth_token = encode_auth_token(user, data.get("email"))
    resp = make_response(jsonify({'success': True, 'user_id': user}))
    resp.set_cookie(
        "auth", 
        auth_token, 
        max_age=60 * 60 * 24 * 10,
        httponly=False,
        secure=False,
        path='/'
    )
    return resp

@app.route('/profile', methods=['GET'])
def profile():
    """API endpoint to get current user profile"""
    from arxivdigest.frontend.database import general as frontend_db
    
    if not hasattr(g, 'loggedIn') or not g.loggedIn or not g.user:
        return make_response(jsonify({'error': 'Not authenticated'}), 401)
    
    user_data = frontend_db.get_user(g.user)
    return make_response(jsonify(user_data), 200)

@app.route('/user/topics', methods=['GET'])
def user_topics():
    """API endpoint for authenticated users to get all topics"""
    if not hasattr(g, 'loggedIn') or not g.loggedIn:
        return make_response(jsonify({'error': 'Not authenticated'}), 401)
    
    topics = db.get_topics()
    return make_response(jsonify({'topics': topics}), 200)

@app.route('/user/categories', methods=['GET'])
def user_categories():
    """API endpoint for authenticated users to get all categories"""
    from arxivdigest.frontend.database import general as frontend_db
    
    if not hasattr(g, 'loggedIn') or not g.loggedIn:
        return make_response(jsonify({'error': 'Not authenticated'}), 401)
    
    categories = frontend_db.getCategoryNames()
    return make_response(jsonify({'categories': categories}), 200)

@app.route('/signup', methods=['POST'])
def signup():
    """API endpoint for user signup"""
    from arxivdigest.frontend.database import general as frontend_db
    from arxivdigest.frontend.models.user import User
    from arxivdigest.frontend.models.errors import ValidationError
    from arxivdigest.frontend.utils import encode_auth_token, send_confirmation_email
    
    data = request.form.to_dict()
    
    try:
        user = User(data)
    except ValidationError as e:
        return make_response(jsonify({'error': e.message}), 400)
    
    if frontend_db.userExist(user.email):
        return make_response(jsonify({'error': 'Email already used by another account'}), 400)
    
    user_id = frontend_db.insertUser(user)
    send_confirmation_email(user.email)
    
    auth_token = encode_auth_token(user_id, user.email)
    resp = make_response(jsonify({'success': True, 'user_id': user_id}))
    resp.set_cookie(
        "auth", 
        auth_token, 
        max_age=60 * 60 * 24 * 10,
        httponly=False,
        secure=False,
        path='/'
    )
    return resp

@app.route('/modify', methods=['POST'])
def modify():
    """API endpoint for updating user profile"""
    from arxivdigest.frontend.database import general as frontend_db
    from arxivdigest.frontend.models.user import User
    from arxivdigest.frontend.models.errors import ValidationError
    
    if not hasattr(g, 'loggedIn') or not g.loggedIn or not g.user:
        return make_response(jsonify({'error': 'Not authenticated'}), 401)
    
    data = request.form.to_dict()
    data['email'] = g.email
    
    if 'notification_interval' in data:
        data['notification_interval'] = str(data['notification_interval'])
    
    topics_str = data.get('topics', '')
    topics_list = [t.strip() for t in topics_str.split(',') if t.strip()]
    
    if 'topics' in data and data['topics']:
        data['topics'] = '\n'.join(topics_list)
    
    categories_str = data.get('categories', '')
    categories_list = [c.strip() for c in categories_str.split(',') if c.strip()]
    if 'categories' in data and data['categories']:
        data['categories'] = '\n'.join(categories_list)
    
    try:
        user = User(data, require_password=False)
    except ValidationError as e:
        return make_response(jsonify({'error': e.message}), 400)
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)
    
    try:
        frontend_db.update_user(g.user, user)
        return make_response(jsonify({'success': True}), 200)
    except Exception as e:
        return make_response(jsonify({'error': f'Database update failed: {str(e)}'}), 500)

@app.route('/user/recommendations', methods=['GET'])
def user_recommendations():
    """API endpoint for getting user recommendations"""
    from arxivdigest.frontend.database import articles as articles_db
    
    if not hasattr(g, 'loggedIn') or not g.loggedIn or not g.user:
        return make_response(jsonify({'error': 'Not authenticated'}), 401)
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    interval = request.args.get('interval', 'thisweek')
    sort_by = request.args.get('sort_by', 'scoredesc')
    
    intervals = {'today': 1, 'thisweek': 7, 'thismonth': 31, 'alltime': 99999}
    interval_days = intervals.get(interval.lower(), 7)
    
    start = (page - 1) * per_page
    articles, total = articles_db.getUserRecommendations(g.user, interval_days, sort_by, start, per_page)
    
    return make_response(jsonify({
        'articles': articles,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    }), 200)

@app.route('/user/saved', methods=['GET'])
def user_saved():
    """API endpoint for getting user saved articles"""
    from arxivdigest.frontend.database import articles as articles_db
    
    if not hasattr(g, 'loggedIn') or not g.loggedIn or not g.user:
        return make_response(jsonify({'error': 'Not authenticated'}), 401)
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    interval = request.args.get('interval', 'alltime')
    sort_by = request.args.get('sort_by', 'scoredesc')
    
    intervals = {'today': 1, 'thisweek': 7, 'thismonth': 31, 'alltime': 99999}
    interval_days = intervals.get(interval.lower(), 99999)
    
    start = (page - 1) * per_page
    articles, total = articles_db.getSavedArticles(g.user, interval_days, sort_by, start, per_page)
    
    return make_response(jsonify({
        'articles': articles,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    }), 200)

@app.route('/user/save/<article_id>', methods=['POST'])
def save_article(article_id):
    """API endpoint for saving/unsaving articles"""
    from arxivdigest.frontend.database import articles as articles_db
    
    if not hasattr(g, 'loggedIn') or not g.loggedIn or not g.user:
        return make_response(jsonify({'error': 'Not authenticated'}), 401)
    
    data = request.get_json()
    saved = data.get('saved', True)
    
    success = articles_db.saveArticle(article_id, g.user, saved)
    
    if success:
        return make_response(jsonify({'success': True}), 200)
    else:
        return make_response(jsonify({'error': 'Failed to save article'}), 400)

@app.route('/logout', methods=['POST'])
def logout():
    """API endpoint for user logout"""
    resp = make_response(jsonify({'success': True}))
    resp.set_cookie('auth', '', expires=0, path='/')
    return resp

@app.route('/passwordChange', methods=['POST'])
def password_change():
    """API endpoint for changing user password"""
    from arxivdigest.frontend.database import general as frontend_db
    
    if not hasattr(g, 'loggedIn') or not g.loggedIn or not g.user:
        return make_response(jsonify({'error': 'Not authenticated'}), 401)
    
    data = request.form
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return make_response(jsonify({'error': 'Missing required fields'}), 400)
    
    user = frontend_db.validatePassword(g.email, current_password)
    if not user:
        return make_response(jsonify({'error': 'Current password is incorrect'}), 400)
    
    frontend_db.updatePassword(g.user, new_password)
    return make_response(jsonify({'success': True}), 200)

@app.route('/user/data', methods=['GET'])
def download_user_data():
    """API endpoint for downloading all user data"""
    from arxivdigest.frontend.database import general as frontend_db
    
    if not hasattr(g, 'loggedIn') or not g.loggedIn or not g.user:
        return make_response(jsonify({'error': 'Not authenticated'}), 401)
    
    user_data = frontend_db.get_all_userdata(g.user)
    return make_response(jsonify(user_data), 200)

@app.route('/feedback', methods=['POST'])
def submit_feedback():
    """API endpoint for submitting feedback"""
    from arxivdigest.frontend.database import general as frontend_db
    
    data = request.get_json()
    feedback_type = data.get('feedback_type', 'Other')
    feedback_text = data.get('feedback_text', '')
    
    user_id = g.user if hasattr(g, 'user') and g.user else None
    
    frontend_db.insertFeedback(user_id, None, feedback_type, feedback_text, {})
    return make_response(jsonify({'success': True}), 200)

@app.route('/user/systems', methods=['GET'])
def user_systems():
    """API endpoint for getting user systems"""
    from arxivdigest.frontend.database import general as frontend_db
    
    if not hasattr(g, 'loggedIn') or not g.loggedIn or not g.user:
        return make_response(jsonify({'error': 'Not authenticated'}), 401)
    
    systems = frontend_db.get_user_systems(g.user)
    return make_response(jsonify({'systems': systems}), 200)

@app.route('/evaluation/system_statistics/<int:system_id>', methods=['GET'])
def system_statistics(system_id):
    """API endpoint for system statistics"""
    from arxivdigest.frontend.database import general as frontend_db
    from arxivdigest.frontend.services import evaluation_service
    from arxivdigest.frontend.utils import is_owner
    from datetime import date, timedelta
    import datetime as dt
    
    if not hasattr(g, 'loggedIn') or not g.loggedIn or not g.user:
        return make_response(jsonify({'error': 'Not authenticated'}), 401)
    
    if not (g.admin or is_owner(g.user, system_id)):
        return make_response(jsonify({'error': 'Not authorized for system.'}), 401)
    
    def to_date(date_str):
        return dt.datetime.strptime(date_str, '%Y-%m-%d').date()
    
    start_date = request.args.get('start_date', date.today() - timedelta(days=30), to_date)
    end_date = request.args.get('end_date', date.today(), to_date)
    aggregation = request.args.get('aggregation', 'day')
    mode = request.args.get('mode', 'article')
    
    if mode == 'article':
        rewards = evaluation_service.get_article_interleaving_reward(start_date, end_date)
    else:
        rewards = evaluation_service.get_topic_interleaving_reward(start_date, end_date)
    
    impress, norm_rewards = evaluation_service.get_normalized_rewards(rewards, start_date, end_date, system_id)
    impressions, labels = evaluation_service.aggregate_data(impress, aggregation)
    norm_rewards, labels = evaluation_service.aggregate_data(norm_rewards, aggregation, sum_result=False)
    
    flat_norm_rewards = []
    for i, period in enumerate(norm_rewards):
        flat_norm_rewards.append([])
        for interleavings in period:
            flat_norm_rewards[i].extend(interleavings)
    
    mean_norm_reward = [sum(norm_rewards) / impressions[i] if impressions[i] else 0
                        for i, norm_rewards in enumerate(flat_norm_rewards)]
    
    return make_response(jsonify({
        'success': True,
        'mean_normalized_reward': mean_norm_reward,
        'impressions': impressions,
        'labels': labels
    }), 200)

@app.route('/evaluation/system_feedback/<int:system_id>', methods=['GET'])
def system_feedback(system_id):
    """API endpoint for system feedback"""
    from arxivdigest.frontend.database import general as frontend_db
    from arxivdigest.frontend.services import evaluation_service
    from arxivdigest.frontend.utils import is_owner
    from arxivdigest.core.config import config_evaluation
    from datetime import date, timedelta
    import datetime as dt
    
    if not hasattr(g, 'loggedIn') or not g.loggedIn or not g.user:
        return make_response(jsonify({'error': 'Not authenticated'}), 401)
    
    if not (g.admin or is_owner(g.user, system_id)):
        return make_response(jsonify({'error': 'Not authorized for system.'}), 401)
    
    def to_date(date_str):
        return dt.datetime.strptime(date_str, '%Y-%m-%d').date()
    
    start_date = request.args.get('start_date', date.today() - timedelta(days=30), to_date)
    end_date = request.args.get('end_date', date.today(), to_date)
    aggregation = request.args.get('aggregation', 'day')
    
    feedback = evaluation_service.get_topic_feedback_amount(start_date, end_date, system_id)
    feedback.update(evaluation_service.get_article_feedback_amount(start_date, end_date, system_id))
    
    result = {}
    for state, data in feedback.items():
        data, label = evaluation_service.aggregate_data(data, aggregation)
        result['labels'] = label
        result[state] = data
    
    for state in config_evaluation['state_weights'].keys():
        result.setdefault(state, [0] * len(result.get('labels', [])))
    
    result.pop('USER_ADDED', None)
    result.pop('USER_REJECTED', None)
    
    return make_response(jsonify(result), 200)

@app.route('/register_system', methods=['POST'])
def register_system():
    """API endpoint for registering a new system"""
    from arxivdigest.frontend.database import general as frontend_db
    from arxivdigest.core.config import CONSTANTS
    
    if not hasattr(g, 'loggedIn') or not g.loggedIn or not g.user:
        return make_response(jsonify({'error': 'Not authenticated'}), 401)
    
    data = request.get_json()
    name = data.get('name', '')
    
    if len(name) > CONSTANTS.max_system_name_length:
        return make_response(jsonify({'error': f'System name must be under {CONSTANTS.max_system_name_length} characters'}), 400)
    
    err, key = frontend_db.insertSystem(name, g.user)
    if err:
        return make_response(jsonify({'error': err}), 400)
    
    return make_response(jsonify({'success': True, 'api_key': key}), 200)

@app.route('/admin/general', methods=['GET'])
def admin_general():
    """API endpoint for admin general statistics"""
    from arxivdigest.frontend.database import admin as admin_db
    
    if not hasattr(g, 'loggedIn') or not g.loggedIn or not g.user:
        return make_response(jsonify({'error': 'Not authenticated'}), 401)
    
    if not g.admin:
        return make_response(jsonify({'error': 'Not authorized'}), 403)
    
    return make_response(jsonify({
        'success': True,
        'users': admin_db.getUserStatistics(),
        'articles': admin_db.getArticleStatistics()
    }), 200)

@app.route('/admin/systems', methods=['GET'])
def admin_systems():
    """API endpoint for admin to get all systems"""
    from arxivdigest.frontend.database import admin as admin_db
    
    if not hasattr(g, 'loggedIn') or not g.loggedIn or not g.user:
        return make_response(jsonify({'error': 'Not authenticated'}), 401)
    
    if not g.admin:
        return make_response(jsonify({'error': 'Not authorized'}), 403)
    
    return make_response(jsonify({'success': True, 'systems': admin_db.getSystems()}), 200)

@app.route('/admin/systems/<int:system_id>/<state>', methods=['PUT'])
def admin_toggle_system(system_id, state):
    """API endpoint for admin to toggle system activation"""
    from arxivdigest.frontend.database import admin as admin_db
    from arxivdigest.core.config import config_email, config_web_address
    from arxivdigest.core.mail.mail_server import MailServer
    
    if not hasattr(g, 'loggedIn') or not g.loggedIn or not g.user:
        return make_response(jsonify({'error': 'Not authenticated'}), 401)
    
    if not g.admin:
        return make_response(jsonify({'error': 'Not authorized'}), 403)
    
    state_bool = state.lower() == 'true'
    if not admin_db.toggleSystem(system_id, state_bool):
        return make_response(jsonify({'result': 'Fail'}), 400)
    
    if state_bool:
        sys = admin_db.getSystem(system_id)
        mail = {
            'to_address': sys['email'],
            'subject': 'System Activation',
            'template': 'systemActivation',
            'data': {
                'name': sys['firstname'] + " " + sys['lastname'],
                'key': sys['api_key'],
                'link': config_web_address
            }
        }
        try:
            server = MailServer(**config_email)
            server.send_mail(**mail)
            server.close()
        except Exception:
            pass
    
    return make_response(jsonify({'result': 'Success'}), 200)

@app.route('/admin/admins', methods=['GET'])
def admin_admins():
    """API endpoint for admin to get all admins"""
    from arxivdigest.frontend.database import admin as admin_db
    
    if not hasattr(g, 'loggedIn') or not g.loggedIn or not g.user:
        return make_response(jsonify({'error': 'Not authenticated'}), 401)
    
    if not g.admin:
        return make_response(jsonify({'error': 'Not authorized'}), 403)
    
    return make_response(jsonify({'success': True, 'admins': admin_db.getAdmins()}), 200)

@app.route('/search', methods=['GET'])
def search():
    """API endpoint for searching articles"""
    from arxivdigest.api.search import search_articles
    from elasticsearch import Elasticsearch
    from arxivdigest.core.config import config_elasticsearch
    
    query = request.args.get('q', '')
    if not query:
        return make_response(jsonify({'error': 'Query parameter required'}), 400)
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    try:
        es_url = config_elasticsearch.get('url', 'http://localhost:9200')
        es = Elasticsearch([es_url])
        
        results = search_articles(es, query, page, per_page)
        return make_response(jsonify(results), 200)
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/', methods=['GET'])
def info():
    """Info response."""
    settings = {
        'user_ids_per_request': config_api['max_userid_request'],
        'max_userinfo_request': config_api['max_userinfo_request'],
        'max_articledata_request': config_api['max_articledata_request'],
        'max_users_per_recommendation': config_api[
            'max_users_per_recommendation'],
        'max_recommendations_per_user': config_api[
            'max_recommendations_per_user'],
        'max_explanation_len': config_api['max_explanation_len'],
        'max_topic_len': CONSTANTS.max_topic_length
    }

    return make_response(jsonify({'info': 'This is the arXivDigest API',
                                  'settings': settings}), 200)


@app.teardown_appcontext
def teardownDb(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


if __name__ == '__main__':
    app.run(port=5002, debug=True)
