from contextlib import closing

from arxivdigest.core import database


def update_semantic_scholar_suggestions(suggestions):
    """Deletes existing Semantic Scholar profile suggestions and inserts new ones for a user."""
    conn = database.get_connection()
    with closing(conn.cursor()) as cur:
        for user_id, user_suggestions in suggestions.items():
            cur.execute('DELETE FROM semantic_scholar_suggestions WHERE user_id = %s', (user_id,))
            for author_id, suggestion in user_suggestions.items():
                sql = '''INSERT INTO semantic_scholar_suggestions (semantic_scholar_id, name, score, user_id)
                         VALUES (%s, %s, %s, %s)'''
                cur.execute(sql, (author_id, suggestion["name"], suggestion["score"], user_id))
                sql = 'UPDATE users SET show_semantic_scholar_popup=true WHERE user_id=%s'
                cur.execute(sql, (user_id,))
        conn.commit()
