# -*- coding: utf-8 -*-
'''This script compares how users have interacted with the recommendations for the differnet systems over a configurable period.
The script has two optional parameters: --startdate and --enddate which controls the period, if no parameters are given the result
will be calculated with all recommendations in the database. 
The script prints the result in a table when its done calculating.
'''

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2018, The ArXivDigest Project'

from mysql import connector
import json
from collections import defaultdict
import argparse
import sys
from datetime import datetime
with open('config.json', 'r') as f:
    config = json.load(f)
    evalconfig = config.get('evaluation_config')


def valid_date(date):
    '''Raises error if input string is not a valid date.'''
    try:
        return datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d')
    except ValueError:
        msg = 'Not a valid date: "%s".' % date
        raise argparse.ArgumentTypeError(msg)


# Parse input arguments to get which period to calculate over
parser = argparse.ArgumentParser()
parser.add_argument('-s',
                    '--startdate',
                    help='The Start Date - format YYYY-MM-DD, Ii not supplied, the script will start at the first available element in the database.',
                    default='0001-01-01',
                    type=valid_date)
parser.add_argument('-e',
                    '--enddate',
                    help='The End Date - format YYYY-MM-DD, if not supplied, the  current date will be used. ',
                    default=datetime.utcnow().strftime('%Y-%m-%d'),
                    type=valid_date)

args = parser.parse_args()


# retrive user interactions for requested period
conn = connector.connect(**config.get('sql_config'))
cur = conn.cursor(dictionary=True)
sql = '''SELECT user_ID, system_ID, DATE(recommendation_date) as date,clicked_email,clicked_web,liked
         FROM user_recommendations WHERE  DATE(recommendation_date) >= %s AND
         DATE(recommendation_date) <= %s'''
cur.execute(sql, (args.startdate, args.enddate))

data = cur.fetchall()

# score system for user interaction
scoreList = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
for item in data:
    # give weighted score to each user interaction
    score = item['clicked_email'] * evalconfig.get('clicked_email_weight')
    score += item['clicked_web'] * evalconfig.get('clicked_web_weight')
    score += item['liked'] * evalconfig.get('liked_weight')

    date = item['date']
    user = item['user_ID']
    system = item['system_ID']
    # add the score to the current day for the current user for the current system
    scoreList[date][user][system] += score

# number of unique userrecommendation list system has been part of
impressions = defaultdict(int)
# wins ties and losses per system
results = defaultdict(lambda: defaultdict(int))
for users in scoreList.values():  # give wins,ties, and loses
    for systems in users.values():
        # at the meeting you said that if only 1 system had the highest score it got a win
        # and if only one system had the lowest score it got a loss, everything else would result in a tie
        minKey = min(systems, key=systems.get)
        maxKey = max(systems, key=systems.get)

        # checks if system is only winner
        if not any([(v == systems[maxKey] and not k == maxKey) for k, v in systems.items()]):
            results[maxKey]['win'] += 1
        else:
            results[maxKey]['tie'] += 1

        # checks if system is only loser
        if not any([(v == systems[minKey] and not k == minKey) for k, v in systems.items()]):
            results[minKey]['loss'] += 1
        elif not minKey == maxKey:  # makes sure not to add a tie to same system twice
            results[minKey]['tie'] += 1
        # give all other systems a tie
        for sys in systems:
            if not(sys == minKey or sys == maxKey):
                results[sys]['tie'] += 1
            impressions[sys] += 1

outcome = {}
# calculate outcome for each system
for system, score in results.items():
    if (score['win']+score['loss']) > 0:
        outcome[system] = score['win']/(score['win']+score['loss'])
    else:
        outcome[system] = -1

# make a table of the results
data = [('systemID', 'impressions', 'wins', 'ties', 'losses', 'outcome')]
for system in sorted(outcome, key=outcome.get, reverse=True):
    item = (system, impressions.get(system, 0),
            results[system]['win'], results[system]['tie'], results[system]['loss'], outcome[system])
    data.append(item)

# print a well formateed table
for i, d in enumerate(data):
    line = '|'.join(str(x).ljust(12) for x in d)
    print(line)
    if i == 0:
        print('-' * len(line))
