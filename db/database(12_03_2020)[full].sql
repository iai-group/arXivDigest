create table categories(
category_id varchar(50) not null,
category varchar(50) not null,
subcategory varchar(50),
category_name varchar(200) not null,
primary key (category_id)
);

create table users(
                      user_id                  int auto_increment,
                      email                    varchar(255) not null unique,
                      salted_hash              char(87) not null,
                      firstname                varchar(255) not null,
                      lastname                 varchar(255) not null,
                      notification_interval    int not null,
                      last_recommendation_date date default '0-0-0',
                      last_email_date          date default '0-0-0',
                      registered               datetime not null,
                      admin                    boolean default false,
                      organization             varchar(255) not null,
                      dblp_profile             varchar(256) DEFAULT '',
                      google_scholar_profile   varchar(256) DEFAULT '',
                      semantic_scholar_profile varchar(256) DEFAULT '',
                      personal_website         varchar(256) DEFAULT '',
                      primary key (user_id)
);

create table user_categories(
user_id int,
category_id varchar(50),
foreign key (category_id) references categories(category_id) on delete cascade,
foreign key (user_id) references users (user_id) on delete cascade,
primary key(user_id, category_id)
);

create table articles(
article_id varchar(50) not null,
title varchar(600) not null,
abstract text not null,
doi varchar(200),
comments text,
license varchar(400),
journal varchar(767),
datestamp date not null,
primary key (article_id)
);

create table article_categories(
article_id varchar(50) not null,
category_id varchar(50) not null,
foreign key (category_id) references categories(category_id) on delete cascade,
foreign key (article_id) references articles(article_id) on delete cascade,
primary key(article_id, category_id)
);

create table article_authors(
author_id int auto_increment,
article_id varchar(50) not null,
firstname varchar(300), 
lastname varchar(300) not null,
foreign key (article_id) references articles(article_id) on delete cascade,
primary key (author_id) 
);

create table author_affiliations(
author_id int not null,
affiliation varchar(400) not null,
foreign key (author_id) references article_authors(author_id) on delete cascade,
primary key (author_id, affiliation)
);

create table systems(
system_id int auto_increment,
api_key char(36) not null unique,
system_name varchar(255) not null unique,
active boolean default true,
admin_user_id int default NULL,
foreign key (user_id) references users(user_id),
primary key(system_id)
);

create table article_recommendations(
user_id int,
article_id varchar(50),
system_id int,
score float not null,
recommendation_date datetime not null,
explanation varchar(1000) not null,
foreign key (system_id) references systems(system_id) on delete cascade,
foreign key (article_id) references articles(article_id),
foreign key (user_id) references users (user_id) on delete cascade,
primary key(user_id, article_id,system_id)
);

create table article_feedback(
user_id int,
article_id varchar(50),
system_id int,
score int not null,
recommendation_date datetime not null,
seen_email datetime default null,
seen_web datetime default null,
clicked_email datetime default null,
clicked_web datetime default null,
saved datetime default null,
trace_save_email char(36),
trace_click_email char(36),
explanation varchar(1000) not null,
foreign key (system_id) references systems(system_id) on delete cascade,
foreign key (article_id) references articles(article_id),
foreign key (user_id) references users (user_id) on delete cascade,
primary key(user_id, article_id)
);

create table feedback(
feedback_id int auto_increment,
user_id int,
article_id varchar(50),
type enum ('Explanation', 'Recommendation', 'Bug', 'Feature', 'Other') not null,
feedback_text varchar(2500) not null,
foreign key (user_id) references users (user_id) on delete cascade,
foreign key (article_id) references articles(article_id) on delete cascade,
primary key (feedback_id)
);

create table topics(
topic_id int auto_increment,
topic varchar(150) not null unique,
filtered boolean default false,
primary key (topic_id)
);

CREATE TABLE user_topics(
user_id int not null,
topic_id int not null,
state enum ('USER_ADDED', 'SYSTEM_RECOMMENDED_ACCEPTED', 'SYSTEM_RECOMMENDED_REJECTED') not null,
interaction_time datetime not null,
foreign key (user_id) references users (user_id) on delete cascade,
foreign key (topic_id) references topics (topic_id) on delete cascade,
primary key (user_id, topic_id)
);

create table topic_recommendations(
user_id            int      not null,
topic_id           int      not null,
system_id          int      not null,
datestamp          datetime not null,
system_score       float    not null,
interleaving_order int,
seen datetime default null,
clicked datetime default null,
foreign key (user_id) references users (user_id) on delete cascade,
foreign key (topic_id) references topics (topic_id) on delete cascade,
foreign key (system_id) references systems (system_id) on delete cascade,
primary key (user_id, topic_id, system_id)
);

create index article_date_index on articles(datestamp);
create index recommendation_date_index on article_recommendations(recommendation_date);
create index article_feedback_date_index on article_feedback(recommendation_date);
create index user_topic_state_index on user_topics(state);
create index topic_date_index on topic_recommendations(datestamp);

create table database_version(
	current_version int not null,
    primary key(current_version)
);

insert into database_version values(1);
