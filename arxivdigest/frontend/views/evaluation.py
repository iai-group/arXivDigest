# -*- coding: utf-8 -*-

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

import datetime
from datetime import date

from flask import Blueprint
from flask import g
from flask import jsonify
from flask import make_response
from flask import request

from arxivdigest.frontend.database import general as general_db
from arxivdigest.frontend.services import evaluation_service
from arxivdigest.frontend.utils import is_owner
from arxivdigest.frontend.utils import requiresLogin

mod = Blueprint('evaluation', __name__)


@mod.route('/evaluation/system_statistics/<int:system_id>', methods=['GET'])
@requiresLogin
def system_statistics(system_id):
    """This endpoint returns system statistics."""

    def to_date(date):
        return datetime.datetime.strptime(date, '%Y-%m-%d').date()

    if not (g.admin or is_owner(g.user, system_id)):
        return make_response(jsonify({'error': 'Not authorized for system.'}),
                             401)

    start_date = date.today() - datetime.timedelta(days=30)
    start_date = request.args.get('start_date', start_date, to_date)
    end_date = request.args.get('end_date', date.today(), to_date)
    aggregation = request.args.get('aggregation', 'day')
    mode = request.args.get('mode', 'article')

    if mode == 'article':
        scores = evaluation_service.get_article_interleaving_scores(start_date,
                                                                    end_date)
    elif mode == 'topic':
        scores = evaluation_service.get_topic_interleaving_scores(start_date,
                                                                  end_date)
    else:
        return make_response(jsonify({'error': 'Unknown mode.'}), 400)

    res = evaluation_service.get_interleaving_results(scores, start_date,
                                                      end_date, system_id)

    impressions, labels = evaluation_service.aggregate_data(res['impressions'],
                                                            aggregation)
    wins, labels = evaluation_service.aggregate_data(res['wins'], aggregation)
    ties, labels = evaluation_service.aggregate_data(res['ties'], aggregation)
    losses, labels = evaluation_service.aggregate_data(res['losses'],
                                                       aggregation)
    outcome = evaluation_service.calculate_outcome(wins, losses)
    return jsonify({'success': True,
                    'wins': wins,
                    'ties': ties,
                    'losses': losses,
                    'outcome': outcome,
                    'impressions': impressions,
                    'labels': labels,
                    })


@mod.route('/evaluation/systems/', methods=['GET'])
@requiresLogin
def system_list():
    """This endpoint returns a list of systems owned by the user."""
    return jsonify({'success': True,
                    'systems': general_db.get_systems(g.user),
                    })
