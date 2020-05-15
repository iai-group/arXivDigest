# -*- coding: utf-8 -*-
from collections import defaultdict

from arxivdigest.core.config import config_evaluation
from arxivdigest.frontend.database import articles as article_db
from arxivdigest.frontend.utils import date_range

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'


def get_interleaving_scores(start_date, end_date):
    """Gets score for each system in each interleaving."""

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


def get_interleaving_results(start_date, end_date, system):
    """Returns a dictionary containing the number of impressions, wins,
    ties and losses for the given system for the supplied period. """
    impressions = {}  # Number of unique interleavings system has been part of.
    wins = {}
    ties = {}
    losses = {}

    scores = get_interleaving_scores(start_date, end_date)
    for date in date_range(start_date, end_date):
        impressions.setdefault(date, 0)
        wins.setdefault(date, 0)
        ties.setdefault(date, 0)
        losses.setdefault(date, 0)
        for user, systems in scores[date].items():
            # If only one system have the highest score it gets a win.
            # If only one system has the lowest score it gets a loss.
            # Everything else results in a tie.
            if system not in systems:
                continue
            impressions[date] += 1

            min_sys = min(systems, key=systems.get)
            max_sys = max(systems, key=systems.get)

            # Check if system is only winner.
            if len([v for v in systems.values() if v == systems[max_sys]]) == 1:
                if max_sys == system:
                    wins[date] += 1
                    continue
            # Check if system is only loser.
            if len([v for v in systems.values() if v == systems[min_sys]]) == 1:
                if min_sys == system:
                    losses[date] += 1
                    continue

            ties[date] += 1

    return {'impressions': impressions, 'wins': wins,
            'ties': ties, 'losses': losses}


def calculate_outcome(wins, losses):
    """Calculate outcome (wins/(wins+losses) for each date.)"""
    outcomes = []
    for win, loss in zip(wins, losses):
        outcome = 0
        if (win + loss) > 0:
            outcome = win / (win + loss)
        outcomes.append(outcome)
    return outcomes


def aggregate_data(data, mode='day', date_format='%Y-%m-%d'):
    """Aggregates the data by time periods.

    :param data: Dictionary of dates to numbers.
    :param mode: Whether to aggregate data for 'day', 'week' or 'month'.
    :param date_format: Format to convert dates to.
    :return: List of aggregated values, and labels for each value
    """
    results = []
    labels = []
    label = None
    old_label = None
    result = 0
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
            result = 0
            old_label = label
        result += value

    labels.append(label)
    results.append(result)
    return results, labels
