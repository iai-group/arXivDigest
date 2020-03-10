import os
from mysql import connector
from arxivdigest.core.config import sql_config
import json
import gzip

def download_dump(dump_folder):
    """Downloads the Semantic Scholar dump with the
    command provided."""
    print('Downloading semantic scholar dump')
    os.system('aws s3 cp --no-sign-request --recursive s3://ai2-s2-research-public/open-corpus/2020-03-01/ ' + dump_folder) 

def load_file_list(dump_folder):
    """Loads a list of the file names in the dump."""
    manifest = open(dump_folder + 'manifest.txt')
    return [line.rstrip() for line in manifest if 'corpus' in line]

def find_topics_from_file(file_path):
    """Finds a set of topics mentioned in the current file."""
    current_topics = set()
    with gzip.open(file_path, 'rt', encoding='utf8') as myfile:
        for line in myfile:
            paper_object = json.loads(line)

            if paper_object.get('entitites'):
                for entity in paper_object.get('entitites'):
                    current_topics.add(entity)

            if paper_object.get('fieldsOfStudy'):
                for field in paper_object.get('fieldsOfStudy'):
                    current_topics.add(field)

    return current_topics

def run_search(datafiles, dump_folder):
    """Iterates through each file and combines topics into one set."""
    topics = set()
    for i, datafile in enumerate(datafiles):
        print('\rProcessed {}/'.format(i+1) + str(len(datafiles)) + ' files...', end='',)
        topics = topics.union(find_topics_from_file(dump_folder + datafile))
    return topics

def insert_topics(conn, topics):
    """Inserts the topics into the database."""
    sql = 'insert into topics values(null,%s,"False")'
    cur = conn.cursor()
    cur.executemany(sql, tuple(topics))

if __name__ == '__main__':
    conn = connector.connect(**sql_config)
    dump_folder = "scripts/data/" 

    #download_dump(dump_folder)
    datafiles = load_file_list(dump_folder)
    topics = run_search(datafiles, dump_folder)
    #insert_topics(conn, topics)

    # print("LENGHT: ", len(topics))
    # print("\n")
    # print(topics)