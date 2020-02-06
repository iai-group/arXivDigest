import requests
from bs4 import BeautifulSoup

def get_pid(auth_url):
    """Returns an author dblp PID from an author dblp profile page link.
    If no response or no result from scraping the web page it returns
    an error."""
    try:
        resp = requests.get(auth_url)
    except Exception as e:
        return e

    parsed_html = BeautifulSoup(resp.content, 'html.parser')
    pid_element = parsed_html.select_one(
        '#main > header > nav > ul > li.share.drop-down > div.body > ul.bullets > li > small')
    if pid_element:
        return pid_element.text
    else:
        return ValueError('Cannot find pid in web page') # TODO return exception?

def get_titles_from_pid(url):#TODO name pid?
    """Returns a list of titles from an author using the authors PID web
    address. Returns error if the author has no titles or request fails."""
    try:
        document = requests.get(url+'.xml')
    except Exception as e: # TODO Return exception?
        return e

    soup = BeautifulSoup(document.content, 'lxml')
    titles = soup.find_all('title')
    if titles:
        return [title.text for title in titles]
    else:
        return ValueError('Author has no titles publicated')  # TODO return exception?

def get_dblp_titles(author_url):
    """Fetches the author pid and then the author paper titles.
    Returns list of titles or the string 'Fail' if requests fail
    or the author has no titles publicated."""
    try:
        author_pid = get_pid(author_url)
        author_titles = get_titles_from_pid(author_pid)
    except Exception as e: # TODO should this really catch?
        return 'Fail'
    return author_titles
