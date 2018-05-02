# -*- coding: utf-8 -*-
__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"

from flask import Blueprint, render_template, request, g, make_response, abort, jsonify
from frontend.database import admin as db
from frontend.utils import requiresLogin
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


@mod.route('/addSystem', methods=['POST'])
@requiresLogin
def addSystem():
    '''Endpoint for inserting new systems, takes the system name from the form and passes it to the database function.'''
    name = request.form['systemName']
    try:
        db.insertSystem(name)
    except mysql.connector.IntegrityError as identifier:
        return render_template('admin.html', systems=db.getSystems(), err="System name already in use.")
    return render_template('admin.html', systems=db.getSystems())


@mod.route('/toggleSystem/<int:systemID>/<state>', methods=['GET'])
@requiresLogin
def toggleSystem(systemID, state):
    '''Endpoint for activating and deactivating systems, sets active-value for system with <systemID> to <state>'''
    state = True if state.lower() == "true" else False
    if db.toggleSystem(systemID, state):
        return jsonify(result='Success')
    return jsonify(result='Fail')
