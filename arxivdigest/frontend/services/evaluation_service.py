# -*- coding: utf-8 -*-
import datetime
from collections import Counter
from collections import defaultdict

from arxivdigest.core.config import config_evaluation
from arxivdigest.frontend.database import articles as article_db
from arxivdigest.frontend.database import general as general_db
from arxivdigest.frontend.utils import date_range

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'


def get_article_interleaving_reward(start_date, end_date):
    """Gets rewards for each system in each interleaving."""

    score_list = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for item in article_db.get_article_feedback_by_date(start_date, end_date):
        score = 0  # give weighted score to each user interaction
        if item['clicked_email']:
            score += 1 * config_evaluation.get('clicked_email_weight')
        if item['clicked_web']:
            score += 1 * config_evaluation.get('clicked_web_weight')
        if item['saved']:
            score += 1 * config_evaluation.get('saved_weight')

        date = item['date']
        user = item['user_id']
        system = item['system_id']

        score_list[date][user][system] += score
    return score_list


def get_topic_interleaving_reward(start_date, end_date):
    """Gets rewards for each system in each interleaving."""
    score_list = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for item in general_db.get_topic_feedback_by_date(start_date, end_date):
        state = item.get('state', '')
        score = config_evaluation['state_weights'].get(state, 0)

        date = item['interleaving_batch']
        user = item['user_id']
        system = item['system_id']

        score_list[date][user][system] += score
    return score_list


def get_normalized_rewards(rewards, start_date, end_date, system,
                           fill_gaps=True):
    """Returns a dictionary containing the number of impressions, wins,
    ties and losses for the given system for the supplied period. """
    impressions = {}  # Number of unique interleavings system has been part of.
    normalized_rewards = {}

    if fill_gaps:
        is_datetime = isinstance(list(rewards.keys())[0], datetime.datetime)
        for date in date_range(start_date, end_date, date_time=is_datetime):
            rewards.setdefault(date, {})

    for date, interleavings in rewards.items():
        impressions.setdefault(date, 0)
        normalized_rewards.setdefault(date, [])
        for user, systems in interleavings.items():
            if system not in systems:
                continue
            impressions[date] += 1
            if sum(systems.values()):
                normalized_rewards[date].append(systems[system] / sum(
                    systems.values()))
            else:
                normalized_rewards[date].append(0)

    return impressions, normalized_rewards


def get_topic_feedback_amount(start_date, end_date, system_id, fill_gaps=True):
    """Gets the amount of feedback given on topics each day."""
    topic_feedback = general_db.get_topic_feedback_by_date(start_date,
                                                           end_date, system_id)
    feedback = defaultdict(Counter)
    for item in topic_feedback:
        feedback[item['state']][item['interleaving_batch']] += 1

    if fill_gaps:
        for state, counts in feedback.items():
            is_datetime = isinstance(list(counts.keys())[0], datetime.datetime)
            for date in date_range(start_date, end_date, date_time=is_datetime):
                feedback[state].setdefault(date, 0)
    return feedback


def get_article_feedback_amount(start_date, end_date, system_id,
                                fill_gaps=True):
    """Gets the amount of feedback given on articles each day."""
    topic_feedback = article_db.get_article_feedback_by_date(start_date,
                                                             end_date,
                                                             system_id)
    feedback = defaultdict(Counter)
    for item in topic_feedback:
        if item['saved']:
            feedback['saved'][item['saved']] += 1
        if item['seen_web']:
            feedback['seen_web'][item['seen_web']] += 1
        if item['clicked_web']:
            feedback['clicked_web'][item['clicked_web']] += 1
        if item['seen_email']:
            feedback['seen_email'][item['seen_email']] += 1
        if item['clicked_email']:
            feedback['clicked_email'][item['clicked_email']] += 1

    if fill_gaps:
        for state, counts in feedback.items():
            is_datetime = isinstance(list(counts.keys())[0], datetime.datetime)
            for date in date_range(start_date, end_date, date_time=is_datetime):
                feedback[state].setdefault(date, 0)
    return feedback


def aggregate_data(data, mode='day', date_format='%Y-%m-%d', sum_result=True):
    """Aggregates the data by time periods.

    :param sum_result: Whether to return the aggregated result as a sum or a list.
    :param data: Dictionary of dates to numbers.
    :param mode: Whether to aggregate data for 'day', 'week' or 'month'.
    :param date_format: Format to convert dates to.
    :return: List of aggregated values, and labels for each value
    """
    results = []
    labels = []
    label = None
    old_label = None
    result = 0 if sum_result else []
    for date, value in sorted(data.items()):
        if mode == 'month':
            label = date.strftime("%B %Y")
        elif mode == 'week':
            label = 'Week ' + str(date.isocalendar()[1]) + date.strftime(" %Y")
        else:
            label = date.strftime(date_format)

        if old_label is None:
            old_label = label

        if label != old_label:
            labels.append(old_label)
            results.append(result)
            result = 0 if sum_result else []
            old_label = label
        if sum_result:
            result += value
        else:
            result.append(value)

    labels.append(label)
    results.append(result)
    return results, labels
