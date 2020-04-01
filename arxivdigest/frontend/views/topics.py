# -*- coding: utf-8 -*-
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import jsonify
from flask import render_template
from flask import request
from flask import url_for

from arxivdigest.frontend.database import general as db
from arxivdigest.frontend.utils import requiresLogin

mod = Blueprint('topics', __name__)

@mod.route('/update_topic/<topic_id>/<state>', methods=['PUT'])
@requiresLogin
def update_topic(topic_id, state):
    """Updates the state of the topics to system approved or rejected."""
    if not db.update_user_topic(topic_id, g.user, state):
        return jsonify(result='fail')
    return jsonify(result='success')

@mod.route('/refresh_topics', methods=['PUT'])
@requiresLogin
def refresh_topics():
    """Refreshe the list of topics on the index page and returns list
    of new topics."""
    db.clear_suggested_user_topics(g.user,'REFRESHED')
    return jsonify(result = db.get_user_topics(g.user))