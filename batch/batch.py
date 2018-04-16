_author_ = "Øyvind Jekteberg and Kristian Gingstad"
_copyright_ = "Copyright 2018, The ArXivDigest Project"

from mail import mailServer
from os.path import commonprefix

from mysql import connector
import database
from datetime import datetime
from random import choice
from uuid import uuid4
import json

with open('../config.json', 'r') as f:
    config = json.load(f)


def TDM(rankings, k):
    '''Teamdraft interleaving. Creates one list of recommendations from lists of recommendations from different systems'''
    L = []
    T = []
    # finds the common prefix for the lists
    prefix = commonprefix(list(rankings.values()))
    L.extend(prefix)
    T.extend([None for x in prefix])  # gives no team credit for common prefix
    # cache to avoid unnecessary "in" checks
    teamIndex = {k: 0 for k in rankings.keys()}
    availableTeams = [k for k, v in rankings.items() if len(v) > 0]
    # add all available teams to the list of teams that haven't added an article this round
    curTeams = list(availableTeams)
    while len(L) < k and availableTeams:
        # select a random team from the list of teams that havent selected this round
        team = choice(curTeams)
        # remove team from this round, so it wont be selected again before the rest have gotten their turn
        curTeams.remove(team)

        R = rankings[team]
        p = teamIndex[team]  # caches previos position to avoid rechecking
        # find highest rated item not already submited by another team
        while R[p] in L and p < k-1:
            p += 1
            if p >= len(R)-1:
                # remove team from list of available if all items are present in the results
                availableTeams.remove(team)
                break
        teamIndex[team] = p
        if not curTeams:  # if all teams have gotten their turn, start a new round
            curTeams = list(availableTeams)

        if R[p] not in L:  # if the item selected by the team is not in the result,
            L.append(R[p])  # add it,
            T.append(team)  # and give the team credit
    return L, T


def sendMail(server, db, articleData, users, emailBatch):
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
    db.setSeenEmail(db, seenMail)


if __name__ == '__main__':
    '''Collects settings from config file and starts batch process'''
    db = connector.connect(**config.get('sql_config'))
    articleData = database.getArticleData(db)
    server = mailServer(**config.get('email_configuration'))
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    batchsize = config.get('users_per_batch')
    i = 0
    while True:
        systemRecs = database.getSystemRecommendations(db, i, batchsize)
        users = database.getUsers(db, i, batchsize)
        if not systemRecs:
            break
        i += batchsize

        recommendatons = []
        emailBatch = {user: [] for user in systemRecs}

        for id, lists in systemRecs.items():
            recs, systems = TDM(lists, config.get('recommendations_per_user'))
            for i in range(0, len(recs)):
                r = (id, recs[i], systems[i], len(recs)-i, now)
                recommendatons.append(r)
                if i < 3:
                    emailBatch[id].append(recs[i])
        database.insertUserRecommendations(db, recommendatons)
        sendMail(server, db, articleData, users, emailBatch)
    db.close()
    server.close()
