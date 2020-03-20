from mysql import connector
from arxivdigest.core.config import config_sql
import re

def insert_topics(conn, topics):
    """inserts the topics into the database topics table."""
    sql = 'insert into topics values(null,%s,0)'
    cur = conn.cursor()
    cur.executemany(sql,topics)
    cur.close()
    conn.commit()

def load_topics(topic_path):
    """Loads a list of topics from the csv file at the provided path.
    Filters out topics that are to long."""
    topics = []
    with open(topic_path, 'r') as topic_file:
        for line in topic_file:
            if len(line) > 50 and not re.match('^[0-9a-zA-Z\-\" ]+$',line):
                continue
            topics.append((line.strip().replace('"',''), ))
    return topics


if __name__ == '__main__':
    conn = connector.connect(**config_sql)
    topic_path = "scripts/data/topics.csv" 
    topics = load_topics(topic_path)
    insert_topics(conn, topics)