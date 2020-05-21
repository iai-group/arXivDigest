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

from arxivdigest.core.config import config_evaluation
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
        rewards = evaluation_service.get_article_interleaving_reward(start_date,
                                                                     end_date)
    elif mode == 'topic':
        rewards = evaluation_service.get_topic_interleaving_reward(start_date,
                                                                   end_date)
    else:
        return make_response(jsonify({'error': 'Unknown mode.'}), 400)

    impress, norm_rewards = evaluation_service.get_normalized_rewards(rewards,
                                                                      start_date,
                                                                      end_date,
                                                                      system_id)

    impressions, labels = evaluation_service.aggregate_data(impress,
                                                            aggregation)

    norm_rewards, labels = evaluation_service.aggregate_data(norm_rewards,
                                                             aggregation,
                                                             sum_result=False)
    flat_norm_rewards = []
    # Flatten sublists.
    for i, period in enumerate(norm_rewards):
        flat_norm_rewards.append([])
        for interleavings in period:
            flat_norm_rewards[i].extend(interleavings)

    mean_norm_reward = [sum(norm_rewards) / impressions[i] if impressions[i]
                        else 0
                        for i, norm_rewards in enumerate(flat_norm_rewards)]
    return jsonify({'success': True,
                    'mean_normalized_reward': mean_norm_reward,
                    'impressions': impressions,
                    'labels': labels,
                    })


@mod.route('/evaluation/system_feedback', methods=['GET'])
@mod.route('/evaluation/system_feedback/<int:system_id>', methods=['GET'])
@requiresLogin
def system_feedback(system_id=None):
    """This endpoint returns system feedback."""

    def to_date(date):
        return datetime.datetime.strptime(date, '%Y-%m-%d').date()

    if not (g.admin or is_owner(g.user, system_id)):
        return make_response(jsonify({'error': 'Not authorized for system.'}),
                             401)

    start_date = date.today() - datetime.timedelta(days=30)
    start_date = request.args.get('start_date', start_date, to_date)
    end_date = request.args.get('end_date', date.today(), to_date)
    aggregation = request.args.get('aggregation', 'day')

    feedback = evaluation_service.get_topic_feedback_amount(start_date,
                                                            end_date,
                                                            system_id)

    feedback.update(evaluation_service.get_article_feedback_amount(start_date,
                                                                   end_date,
                                                                   system_id))
    json = {}
    for state, data in feedback.items():
        data, label = evaluation_service.aggregate_data(data, aggregation)
        json['labels'] = label
        json[state] = data
    for state in config_evaluation['state_weights'].keys():
        json.setdefault(state, [0] * len(json.get('labels', [])))
    json.pop('USER_ADDED')
    json.pop('USER_REJECTED')
    return jsonify(json)


@mod.route('/evaluation/systems/', methods=['GET'])
@requiresLogin
def system_list():
    """This endpoint returns a list of systems owned by the user."""
    return jsonify({'success': True,
                    'systems': general_db.get_systems(g.user),
                    })
