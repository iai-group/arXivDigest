from urllib import request, parse, error
import json
from random import choice
api_keys = ['ed679075-21aa-4507-9179-8e27fbebd433',
            '3afcae74-c52f-48be-9a0a-f5a25e8016f6',
            '5c0bb1d2-bf1b-497a-be10-63adc7b5c6a2',
            'fe0e32ec-ca7f-4604-b6e5-5f59a85d1450']

link = "https://api.arxivdigest.org/"


def users(start, api_key):
    req = request.Request('%susers?from=%d' % (link, start),
                          headers={"api_key": api_key})
    resp = request.urlopen(req)
    return json.loads(resp.read())


def articles(api_key):
    req = request.Request('%sarticles' % link, headers={"api_key": api_key})
    try:
        resp = request.urlopen(req)
    except error.HTTPError as e:
        print(e.read())
    return json.loads(resp.read())


def sendRecommendations(data, api_key):
    data = json.dumps({'recommendations': data}).encode('utf8')
    req = request.Request(link+"recommendation", data=data, headers={
                          'Content-Type': 'application/json', "api_key": api_key})
    resp = request.urlopen(req)

if __name__ == '__main__':
    u = users(0, api_keys[0])

"""
for key in api_keys:
    articlelist = articles(key)['articles']['article_ids']
    i = 0
    while True:
        userlist = users(i, key)['users']
        data = {}
        for user in userlist['user_ids']:
            data[user] = []
            articleSet = set()
            while len(articleSet) < 10:
                articleSet.add(choice(articlelist))
            articleSet = list(articleSet)
            for i in range(0, 10):
                rec = {"article_id": articleSet[i], "score": i}
                data[user].append(rec)
            if len(data) == 100:
                sendRecommendations(data, key)
                data = {}
        i += 10000
        if i > userlist['num']:
            sendRecommendations(data, key)
            break
"""