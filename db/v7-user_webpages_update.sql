DROP TABLE IF EXISTS user_webpages;

ALTER TABLE users
    ADD dblp_profile varchar(256) DEFAULT '',
    ADD google_scholar_profile varchar(256) DEFAULT '',
    ADD semantic_scholar_profile varchar(256) DEFAULT '',
    ADD personal_website varchar(256) DEFAULT '';
