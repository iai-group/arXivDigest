from frontend.scrape_keywords.dblp import get_dblp_titles

def find_author_titles(author_url):
    """Checks the provided link and fetches keywords from the required
    website. If site is not supported or the fetching fails, return
    empty string."""
    if 'dblp.' in author_url:
        author_titles = get_dblp_titles(author_url)
        if author_titles != 'Fail':
            return author_titles
        return ""
    else:
        return ""