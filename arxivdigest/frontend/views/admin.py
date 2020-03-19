# -*- coding: utf-8 -*-
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

from flask import abort
from flask import Blueprint
from flask import g
from flask import jsonify
from flask import render_template
from flask import request

from arxivdigest.core.config import config_email
from arxivdigest.core.config import config_web_address
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
    return jsonify({'success': True, 'systems': db.getSystems()})


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
                'data': {'name': sys['firstname'] + " " + sys['lastname'],
                         'key': sys['api_key'],
                         'link': config_web_address}}

        Server = MailServer(**config_email)
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
