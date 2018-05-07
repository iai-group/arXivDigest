# -*- coding: utf-8 -*-
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2018, The ArXivDigest Project'

from flask import Blueprint, render_template, request, g, make_response, abort, jsonify
from frontend.database import admin as db
from frontend.utils import requiresLogin
from frontend.config import config
from mail import mailServer
import mysql
mod = Blueprint('admin', __name__)


@mod.before_request
def before_request():
    if not g.loggedIn or not db.isAdmin(g.user):
        return abort(404)
    return None


@mod.route('/', methods=['GET'])
@requiresLogin
def admin():
    '''Returns the adminpage'''
    return render_template('admin.html')


@mod.route('/systems/get', methods=['GET'])
@requiresLogin
def getSystems():
    '''Returns list of systems from db'''
    return jsonify({'success': True, 'systems': db.getSystems()})


@mod.route('/admins/get', methods=['GET'])
@requiresLogin
def getAdmins():
    '''Returns list of admins from db'''
    return jsonify({'success': True, 'admins': db.getAdmins()})


@mod.route('/systems/toggleActive/<int:systemID>/<state>', methods=['GET'])
@requiresLogin
def toggleSystem(systemID, state):
    '''Endpoint for activating and deactivating systems, sets active-value for system with <systemID> to <state>'''
    state = True if state.lower() == "true" else False
    if not db.toggleSystem(systemID, state):
        return jsonify(result='Fail')
    if state == True:
        sys = db.getSystem(systemID)
        mail = {'toadd': sys['email'],
                'subject': 'System Activation',
                'template': 'systemActivation',
                'data': {'name': sys['contact_name'],
                         'key': sys['api_key']}}

        Server = mailServer(**config.get('email_configuration'))
        try:
            Server.sendMail(**mail)
        except Exception as e:
            return jsonify(result='Success', err='Email error')
        finally:
            Server.close()
    return jsonify(result='Success')


@mod.route('/general', methods=['GET'])
@requiresLogin
def general():
    '''This endpoint returns general stats for the project'''
    return jsonify({'success': True,
                    'users': db.getUserStatistics(),
                    'articles': db.getArticleStatistics()
                    })
