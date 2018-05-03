# -*- coding: utf-8 -*-
__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"

from flask import Blueprint, render_template, request, g, make_response, abort, jsonify
from frontend.database import admin as db
from frontend.utils import requiresLogin
from frontend import mailServer

import mysql
mod = Blueprint('admin', __name__)


@mod.before_request
def before_request():
    if not db.isAdmin(g.user):
        return abort(404)
    return None


@mod.route('/', methods=['GET'])
@requiresLogin
def admin():
    '''Returns the adminpage'''
    return render_template('admin.html', systems=db.getSystems())


@mod.route('/toggleSystem/<int:systemID>/<state>', methods=['GET'])
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

        mailServer.sendMail(**mail)
    return jsonify(result='Success')
