# -*- coding: utf-8 -*-
'''This script that combines the recommendations from the experimental recommender systems and inserts the combined ranking, for each user, into the database.
 It also sends out the digest emails to users.
'''
__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"
import sys
sys.path.append("..")
from mail import mailServer
from mysql import connector
import database as db
from tdm import multiLeaver
from datetime import datetime
from random import choice
from uuid import uuid4
import json

with open('../config.json', 'r') as f:
    config = json.load(f)


def sendMail(server, conn, articleData, users, emailBatch):
    '''Creates mail content and sends it to send mail function'''
    seenMail = []
    link = config.get('webaddress')
    for user, recommendations in emailBatch.items():
        data = {'name': users[user]['name'], 'articles': []}
        for rec in recommendations:
            clickTrace = str(uuid4())
            likeTrace = str(uuid4())
            article = articleData.get(rec)
            data['articles'].append(
                {'title': article.get("title"),
                 'authors': article.get("authors"),
                 'readlink': link+'mail/read/%s/%s/%s' % (user, rec, clickTrace),
                 'likelink': link+'mail/like/%s/%s/%s' % (user, rec, likeTrace)
                 })
            seenMail.append((clickTrace, likeTrace, user, rec,))
        if len(data['articles']) > 0:
            server.sendMail(users[user]['email'],
                            'ArXiv Digest', data, 'notification')
    conn.setSeenEmail(conn, seenMail)


if __name__ == '__main__':
    '''Collects settings from config file and starts batch process'''
    conn = connector.connect(**config.get('sql_config'))
    ml = multiLeaver(config.get('recommendations_per_user'),
                     config.get('systems_interleaved_per_user'))
    articleData = db.getArticleData(conn)
    server = mailServer(**config.get('email_configuration'))
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    batchsize = config.get('users_per_batch')
    i = 0
    while True:
        systemRecs = db.getSystemRecommendations(conn, i, batchsize)
        users = db.getUsers(conn, i, batchsize)
        if not systemRecs:
            break
        i += batchsize

        recommendations = []
        emailBatch = {user: [] for user in systemRecs}

        for id, lists in systemRecs.items():
            recs, systems = ml.TDM(lists, )
            for i in range(0, len(recs)):
                r = (id, recs[i], systems[i], len(recs)-i, now)
                recommendations.append(r)
                if i < 3:
                    emailBatch[id].append(recs[i])
        db.insertUserRecommendations(conn, recommendations)
        sendMail(server, conn, articleData, users, emailBatch)
    conn.close()
    server.close()
