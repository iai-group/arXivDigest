rename table system_recommendations to article_recommendations;
rename table user_recommendations to article_feedback;

create table topic_recommendations(
                                      recommendation_id  int auto_increment,
                                      user_id            int      not null,
                                      topic_id           int      not null,
                                      system_id          int      not null,
                                      datestamp          datetime not null,
                                      system_score       float    not null,
                                      interleaving_order int,
                                      seen boolean default false,
                                      clicked boolean default false,
                                      foreign key (user_id) references users (user_id) on delete cascade,
                                      foreign key (topic_id) references topics (topic_id) on delete cascade,
                                      foreign key (system_id) references systems (system_id) on delete cascade,
                                      primary key (recommendation_id)
);

create index article_date_index on articles (datestamp);
create index recommendation_date_index on article_recommendations(recommendation_date);
create index article_feedback_date_index on article_feedback(recommendation_date);
create index user_topic_state_index on user_topics(state);
create index topic_date_index on topic_recommendations(datestamp);


alter table categories
change column category_ID category_id varchar(50) not null;

alter table users
change column user_ID user_id int auto_increment;

alter table user_categories
change column user_ID user_id int,
change column category_ID category_id varchar(50);


alter table articles
change column article_ID article_id varchar(50) not null;

alter table article_categories
change column article_ID article_id varchar(50) not null,
change column category_ID category_id varchar(50) not null;


alter table article_authors
change column author_ID author_id int auto_increment,
change column article_ID article_id varchar(50) not null;


alter table author_affiliations
change column author_ID author_id int not null;


alter table systems
change column system_ID system_id int auto_increment,
change column user_ID user_id int default NULL;


alter table article_recommendations
change column user_ID user_id int,
change column article_ID article_id varchar(50),
change column system_ID system_id int;


alter table article_feedback
change column user_ID user_id int,
change column article_ID article_id varchar(50),
change column system_ID system_id int;


alter table feedback
change column feedback_ID feedback_id int auto_increment,
change column user_ID user_id int,
change column article_ID article_id varchar(50);
