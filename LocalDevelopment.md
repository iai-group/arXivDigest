# Local development guide

## Initial setup

1. Clone repository.
2. Make sure [Python 3](https://www.python.org/downloads/) is installed.
3. Install a [MySQL server](https://www.mysql.com/)
4. Execute all sql scripts in [db/](db/) starting with [db/database.sql](db/database.sql) then V1, V2, etc...
4. Run the command  ```pip install -r ./requirements.txt``` while inside ``arXivDigest/`` to download the required python packages.
5. (Optional) Install an [Elasticsearch](https://www.elastic.co/) server if working on the sample system
6. Make sure that the [config.json](/config.json) is configured with the correct credentials for your MySQL server

## Individual parts

### Frontend

Should be run from the root repository folder: ``python ./frontend/app.py``
Make sure that port 80 is free or configure the frontend dev_port in [config.json](/config.json)

### API

Should be run from the root repository folder: ``python ./api/app.py``
Make sure that port 5000 is free or configure the api dev_port in [config.json](/config.json)

### Scraper

Is run by running storeMetadata.py: ``python storeMetadata.py``
Articles are not released every day, so this script will not always insert any articles. 

### Interleaver

Is run by running interleave.py: ``python interleave.py``

### Evaluation

Is run by running evaluation.py: ``python evaluation.py``
