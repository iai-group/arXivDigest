__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"

from flask import Blueprint, request, make_response, g, jsonify, render_template, redirect
import math
from frontend.database import articles as db
from frontend.utils import requiresLogin, pageinate

mod = Blueprint('articles', __name__)


def genArticleList(getArticles):
    '''Returns dictionary with: current interval selection, number of articles per page(5), current page, 
    current sort method, pages for pagination div,  number of articles, the articles, values for timedropdown
    and values for sortdropdown. Is a helper function used for showing long list of articles like in index and likedArticles'''
    pageNr = request.args.get('pageNr', 1, type=int)
    if pageNr < 1:
        pageNr = 1
    articlesPerPage = request.args.get('articlesPerPage', 5, type=int)
    if articlesPerPage < 1:
        articlesPerPage = 5
    sortBy = request.args.get('sortBy', 'scoreDesc').lower()
    intervals = {'today': 1, 'thisweek': 7, 'thismonth': 31, 'alltime': 99999}

    def intervalCheck(value):
        if value.lower() not in intervals:
            raise ValueError
        return value
    interval = request.args.get('interval', 'thisWeek', type=intervalCheck)

    intervalDays = intervals.get(interval.lower(), 7)
    start = (pageNr-1)*articlesPerPage
    articles, count = getArticles(g.user, intervalDays, sortBy,
                                  start, articlesPerPage)

    db.seenArticle([(x['article_ID'], g.user) for x in articles])

    numberOfPages = math.ceil(count/articlesPerPage)
    pages = pageinate(pageNr, numberOfPages, 15)

    return {'interval': interval.lower(),
            'articlesPerPage': articlesPerPage,
            'currentPage': pageNr,
            'sortBy': sortBy,
            'pages': pages,
            'count': count,
            'articles': articles,
            'timeDropDown': [('today', 'Today'), ('thisweek', 'This week'), ('thismonth', 'This month'), ('alltime', 'All time')],
            'sortDropDown': [('titleasc', 'Title ascending'), ('titledesc', 'Title descending'), ('scoreasc', 'Score ascending'), ('scoredesc', 'Score descending')]
            }


@mod.route('/')
@requiresLogin
def index():
    '''Returns index page with list of articles'''
    return render_template('index.html', endpoint='articles.index', ** genArticleList(db.getUserRecommendations))


@mod.route('/likedArticles', methods=['GET'])
@requiresLogin
def likedArticles():
    '''Returns likedarticles page with list of liked articles'''
    return render_template('likes.html', endpoint='articles.likedArticles', ** genArticleList(db.getLikedArticles))


@mod.route('/like/<articleID>/<state>', methods=['GET'])
@requiresLogin
def like(articleID, state):
    '''Endpoint for liking and unliking articles, sets like-value for article with <articleID> to <state>'''
    state = True if state.lower() == "true" else False
    if db.likeArticle(articleID, g.user, state):
        return jsonify(result='Success')
    return jsonify(result='Fail')


@mod.route('/mail/like/<int:userID>/<string:articleID>/<uuid:trace>', methods=['GET'])
def likeEmail(articleID, userID, trace):
    '''Endpoint for liking an article directly from from email. 
    Uses a combination of 3 values to make randomly guessing and bruteforcing almost impossible.'''
    return db.likeArticleEmail(articleID, userID, str(trace))


@mod.route('/mail/read/<int:userID>/<string:articleID>/<uuid:trace>', methods=['GET'])
def readEmail(articleID, userID, trace):
    '''Records clicks from email'''
    db.clickedArticleEmail(articleID, userID, str(trace))
    return redirect('https://arxiv.org/abs/%s' % articleID)


@mod.route('/click/<string:articleId>', methods=['GET'])
@requiresLogin
def click(articleId):
    '''Records if user clicks an article, redirects user to arXiv infopage for article or the article pdf depending on whether <pdf> is true or false'''
    db.clickArticle(articleId, g.user)
    pdf = request.args.get('pdf', False, type=lambda x: x.lower() == 'true')
    if pdf:
        return redirect('https://arxiv.org/pdf/%s.pdf' % articleId)
    return redirect('https://arxiv.org/abs/'+articleId)
