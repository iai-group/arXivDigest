# -*- coding: utf-8 -*-
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

import math

from flask import Blueprint
from flask import flash
from flask import g
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from arxivdigest.frontend.database import articles as db
from arxivdigest.frontend.utils import pageinate
from arxivdigest.frontend.utils import requiresLogin

mod = Blueprint('articles', __name__)


def genArticleList(getArticles):
    '''Returns dictionary with: current interval selection, number of articles per page(5), current page, 
    current sort method, pages for pagination div,  number of articles, the articles, values for timedropdown
    and values for sortdropdown. Is a helper function used for showing long list of articles save in index and savedArticles'''
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

    db.seenArticle([(x['article_id'], g.user) for x in articles])

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


@mod.route('/savedArticles', methods=['GET'])
@requiresLogin
def savedArticles():
    '''Returns savedarticles page with list of saved articles'''
    return render_template('saves.html', endpoint='articles.savedArticles', ** genArticleList(db.getSavedArticles))


@mod.route('/save/<articleID>/<state>', methods=['PUT'])
@requiresLogin
def save(articleID, state):
    '''Endpoint for liking and unliking articles, sets save-value for article with <articleID> to <state>'''
    state = True if state.lower() == "true" else False
    if db.saveArticle(articleID, g.user, state):
        return jsonify(result='Success')
    return jsonify(result='Fail')


@mod.route('/mail/save/<int:userID>/<string:articleID>/<uuid:trace>', methods=['GET'])
def saveEmail(articleID, userID, trace):
    '''Endpoint for liking an article directly from from email. 
    Uses a combination of 3 values to make randomly guessing and bruteforcing almost impossible.'''
    success = db.saveArticleEmail(articleID, userID, str(trace))
    if not success:
        return "Some error occurred."
    if g.loggedIn:
        flash("Saved article %s" % articleID, "success")
        return redirect(url_for("articles.index"))
    flash("Saved article %s" % articleID, "success")
    return redirect(url_for("general.loginPage"))


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
