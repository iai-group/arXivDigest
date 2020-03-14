# TODO this file should not be in the repository at all, should just be sent by mail
# TODO The other old scripts should be removed, and sent in the same mail if needed.


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
                                      foreign key (user_id) references users (user_id) on delete cascade,
                                      foreign key (topic_id) references topics (topic_id) on delete cascade,
                                      foreign key (system_id) references systems (system_id) on delete cascade,
                                      primary key (recommendation_id)
);

create index user_email_index on users (email); # TODO unique creates index
create index article_date_index on articles (datestamp);
create index recommendation_date_index on article_recommendations(recommendation_date);
create index article_feedback_date_index on article_feedback(recommendation_date);
create index topic_index on topics (topic); # TODO unique creates index
create index user_topic_state_index on user_topics(state);
create index topic_date_index on topic_recommendations(datestamp);


alter table categories
change column category_ID category_id varchar(50) not null;

alter table users
change column user_ID user_id int auto_increment;

alter table user_categories
drop foreign key user_categories_ibfk_2,
change column user_ID user_id int,
add constraint user_categories_ibfk_2_2
foreign key (user_id) references users (user_id)
on delete cascade;

alter table user_categories
    drop foreign key user_categories_ibfk_1, # TODO is this really needed? Renamed my tables with the foreignkey active
    change column category_ID category_id varchar(50),
    add constraint user_categories_ibfk_1_2
foreign key (category_id) references categories (category_id)
on delete cascade;


alter table articles
change column article_ID article_id varchar(50) not null;

alter table article_categories
    drop foreign key article_categories_ibfk_2,
    change column article_ID article_id varchar(50) not null,
    add constraint user_categories_ibfk_1_2 # TODO user_categories?
foreign key (article_id) references articles (article_id)
on delete cascade;

alter table article_categories
    drop foreign key article_categories_ibfk_1,
    change column category_ID category_id varchar(50) not null,
    add constraint user_categories_ibfk_2_2 # TODO user_categories?
foreign key (category_id) references categories (category_id)
on delete cascade;


alter table article_authors
change column author_ID author_id int auto_increment;

alter table article_authors
    drop foreign key article_authors_ibfk_1,
    change column article_ID article_id varchar(50) not null,
    add constraint user_categories_ibfk_1_2 # TODO user_categories?
foreign key (article_id) references articles (article_id)
on delete cascade;


alter table author_affiliations
    drop foreign key author_affiliations_ibfk_1,
    change column author_ID author_id int not null,
    add constraint user_categories_ibfk_1_2 # TODO user_categories?
foreign key (author_id) references article_authors (author_id)
on delete cascade;


alter table systems
change column system_ID system_id int auto_increment;

alter table systems
drop foreign key systems_ibfk_1,
change column user_ID user_id int default NULL,
add constraint systems_ibfk_1_2
foreign key (user_id) references users (user_id);


alter table article_recommendations
drop foreign key article_recommendations_ibfk_3,
change column user_ID user_id int,
add constraint article_recommendations_ibfk_3_2
foreign key (user_id) references users (user_id)
on delete cascade;

alter table article_recommendations
drop foreign key article_recommendations_ibfk_2,
change column article_ID article_id varchar(50),
add constraint article_recommendations_ibfk_2_2
foreign key (article_id) references articles (article_id);

alter table article_recommendations
drop foreign key article_recommendations_ibfk_1,
change column system_ID system_id int,
add constraint article_recommendations_ibfk_1_2
foreign key (system_id) references systems (system_id)
on delete cascade;


alter table article_feedback
drop foreign key article_feedback_ibfk_3,
change column user_ID user_id int,
add constraint article_feedback_ibfk_3_2
foreign key (user_id) references users (user_id)
on delete cascade;

alter table article_feedback
drop foreign key article_feedback_ibfk_2,
change column article_ID article_id varchar(50),
add constraint article_feedback_ibfk_2_2
foreign key (article_id) references articles (article_id);

alter table article_feedback
drop foreign key article_feedback_ibfk_1,
change column system_ID system_id int,
add constraint article_feedback_ibfk_1_2
foreign key (system_id) references systems (system_id)
on delete cascade;


alter table feedback
change column feedback_ID feedback_id int auto_increment;

alter table feedback
drop foreign key feedback_ibfk_1,
change column user_ID user_id int,
add constraint feedback_ibfk_1_2
foreign key (user_id) references users (user_id)
on delete cascade;

alter table feedback
drop foreign key feedback_ibfk_2,
change column article_ID article_id varchar(50),
add constraint feedback_ibfk_2_2
foreign key (article_ID) references articles (article_id)
on delete cascade;
