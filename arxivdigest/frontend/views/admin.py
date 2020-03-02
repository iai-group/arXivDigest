# -*- coding: utf-8 -*-
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2018, The ArXivDigest Project'

from flask import abort
from flask import Blueprint
from flask import g
from flask import jsonify
from flask import render_template
from flask import request

from arxivdigest.core.config import email_config
from arxivdigest.core.mail.mail_server import MailServer
from arxivdigest.frontend.database import admin as db
from arxivdigest.frontend.utils import requiresLogin

mod = Blueprint('admin', __name__)


@mod.before_request
def before_request():
    if not g.loggedIn or not db.isAdmin(g.user):
        return abort(404)
    return None


@mod.route('/', methods=['GET'])
@requiresLogin
def admin():
    """Returns the adminpage"""
    return render_template('admin.html')


@mod.route('/systems/get', methods=['GET'])
@requiresLogin
def getSystems():
    """Returns list of systems from db"""
    systems = db.getSystems()
    full_systems = []
    for system in systems:
        user = db.get_system_user_data(g.user)
        system = {
            'system_ID': system['system_ID'],
            'system_name': system['system_name'],
            'contact_name': user['firstName'] + ' '+ user['lastName'],
            'company_name': user['company'],
            'email': user['email'],
            'api_key': system['api_key'],
            'active': system['active']
        }
        full_systems.append(system)
    return jsonify({'success': True, 'systems': full_systems})


@mod.route('/admins/get', methods=['GET'])
@requiresLogin
def getAdmins():
    """Returns list of admins from db"""
    return jsonify({'success': True, 'admins': db.getAdmins()})


@mod.route('/systems/toggleActive/<int:systemID>/<state>', methods=['GET'])
@requiresLogin
def toggleSystem(systemID, state):
    """Endpoint for activating and deactivating systems, sets active-value
     for system with <systemID> to <state>"""
    state = True if state.lower() == "true" else False
    if not db.toggleSystem(systemID, state):
        return jsonify(result='Fail')
    if state:
        sys = db.getSystem(systemID)
        mail = {'to_address': sys['email'],
                'subject': 'System Activation',
                'template': 'systemActivation',
                'data': {'name': sys['contact_name'],
                         'key': sys['api_key'],
                         'link': request.url_root}}

        Server = MailServer(**email_config)
        try:
            Server.send_mail(**mail)
        except Exception as e:
            return jsonify(result='Success', err='Email error')
        finally:
            Server.close()
    return jsonify(result='Success')


@mod.route('/general', methods=['GET'])
@requiresLogin
def general():
    """This endpoint returns general stats for the project"""
    return jsonify({'success': True,
                    'users': db.getUserStatistics(),
                    'articles': db.getArticleStatistics()
                    })
