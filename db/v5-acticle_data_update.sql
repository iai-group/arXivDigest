drop table  if exists topics;

create table topics( --table for topics with their topic ids from semantic scholar
topic_ID int not null,
topic varchar(200) not null,
primary key (topic_ID)
);

create table article_topics( --links several topics to articles
    article_ID varchar(50) not null,
    topic_ID int not null
    foreign key (topic_ID) references topics(topic_ID) on delete cascade,
    foreign key (article_ID) references articles(article_ID) on delete cascade,
    primary key(article_ID,topic_ID)
);

ALTER TABLE articles
ADD venue varchar(1000); --venue from semantic scholar

ALTER TABLE articles
ADD semantic_scholar_ID varchar(100); --adds the semantic scholar id to the articles

ALTER TABLE article_authors
ADD semantic_scholar_ID int; --adds the author id from semantic scholar to the authors

create table article_references(
    article_ID varchar(50) not null, --arxiv article id
    reference_ID varchar(100), --the paperid from semantic scholar, can use this in semantic scholar api later
    reference varchar(1000) not null, --title of the referenced paper
    primary key(article_ID,reference_ID),
    foreign key(article_ID) references articles(article_ID) on delete cascade
);