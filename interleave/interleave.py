# -*- coding: utf-8 -*-
'''This script that combines the recommendations from the experimental recommender systems and inserts the combined ranking, for each user, into the database.
 It also sends out the digest emails to users.
'''
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2018, The ArXivDigest Project'
import os
import json
from uuid import uuid4
from random import choice
from datetime import datetime
import calendar
from tdm import multiLeaver
import database as db
from mysql import connector
import sys

try:
    import mail
except:
    sys.path.append(os.path.abspath('../scripts/'))
from mail import mailServer

with open('../config.json', 'r') as f:
    config = json.load(f)
    interleaveConfig = config.get('interleave_config')
    recommendationsPerUser = interleaveConfig.get('recommendations_per_user')
    systemsPerUser = interleaveConfig.get('systems_multileaved_per_user')
    batchsize = interleaveConfig.get('users_per_batch')


def multiLeaveRecommendations(systemRecommendations):
    '''Multileaves the given systemRecommendations and returns a list of userRecommendations. '''
    userRecommendations = []
    for userID, lists in systemRecommendations.items():
        # mulileave system recommendations
        recs, systems = ml.TDM(lists)
        # prepare results for database insertion
        for i in range(0, len(recs)):
            score = len(recs)-i

            rec = (userID, recs[i]["article_ID"],
                   systems[i], recs[i]["explanation"],  score, now)

            userRecommendations.append(rec)
    return userRecommendations


def topN(articles, n):
    '''Returns the top n scored articleIDs.'''
    if not articles:
        return []
    maxScore = max(articles.values())
    return [id for id, score in articles.items() if score > maxScore-n]


def sendMail():
    '''Sends notification emails to users about new recommendations'''
    articleData = db.getArticleData(conn)
    path = os.path.join(os.path.dirname(__file__), 'templates')
    server = mailServer(**config.get('email_configuration'), templates=path)
    link = interleaveConfig.get('webaddress')

    for i in range(0, maxUserID+batchsize, batchsize):
        mails = []
        seenMail = []
        users = db.getUsers(conn, i, batchsize)
        userRecommendations = db.getUserRecommendations(conn, i, batchsize)
        if not userRecommendations:
            continue
        for userID, user in users.items():
            mail = {'toadd': user['email'],
                    'subject': 'ArXiv Digest',
                    'data':  {'name': user['name'], 'articles': [], 'link': link},
                    'template': 'weekly'}
            # find the top articles for each user
            topArticles = {}
            if user['notification_interval'] == 1:
                date = datetime.utcnow().date()
                recs = userRecommendations[userID][date]
                topArticles[date.weekday()] = topN(recs, 3)
            elif datetime.utcnow().weekday() == 4:
                for day, articles in userRecommendations[userID].items():
                    topArticles[day.weekday()] = topN(articles, 3)
            if not any(topArticles.values()):  # skip user if there user has no recommendations
                continue
            # create mail data for each article
            mailData = []
            for day, articleIDs in topArticles.items():
                articleInfo = []
                for articleID in articleIDs:
                    article = articleData.get(articleID)
                    clickTrace = str(uuid4())
                    likeTrace = str(uuid4())
                    articleInfo.append({'title': article.get('title'),
                                        'authors': article.get('authors'),
                                        'readlink': '%smail/read/%s/%s/%s' % (link, user, articleID, clickTrace),
                                        'likelink': '%smail/like/%s/%s/%s' % (link, user, articleID, likeTrace)
                                        })

                    # mark added articles as seen in mail
                    seenMail.append((clickTrace, likeTrace, userID, articleID))

                mailData.append((calendar.day_name[day], articleInfo, day))
            mailData.sort(key=lambda x: x[2])
            mail['data']['articles'] = mailData
            # add mail to send mail queue
            mails.append(mail)

        if not mails:
            continue  # skip sending mail if none of the users should receive any mail
        # mark all articles as seen in database and send all mails
        db.setSeenEmail(conn, seenMail)
        for mail in mails:
            server.sendMail(**mail)

    server.close()


if __name__ == '__main__':
    '''Multileaves system recommendations and inserts the new lists into the database, then sends notification email to user.'''
    conn = connector.connect(**config.get('sql_config'))
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    ml = multiLeaver(recommendationsPerUser, systemsPerUser)
    maxUserID = db.getHighestUserID(conn)
    # range-stop is bigger than maxUserID to ensure all users are found
    for i in range(0, maxUserID+batchsize, batchsize):
        systemRecs = db.getSystemRecommendations(conn, i, batchsize)
        if systemRecs:
            userRecommendations = multiLeaveRecommendations(systemRecs)
            db.insertUserRecommendations(conn, userRecommendations)

    sendMail()
    conn.close()
