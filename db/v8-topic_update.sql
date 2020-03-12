create table topics
(
    topic_id int auto_increment,
    topic    varchar(150) not null unique,
    filtered boolean default false,
    primary key (topic_id)
);

CREATE TABLE user_topics
(
    user_id          int,
    topic_id         int,
    state            enum ('USER_ADDED', 'SYSTEM_RECOMMENDED_ACCEPTED', 'SYSTEM_RECOMMENDED_REJECTED') not null,
    interaction_time datetime                                                                          not null,
    foreign key (user_id) references users (user_ID) on delete cascade,
    foreign key (topic_id) references topics (topic_id) on delete cascade,
    primary key (user_id, topic_id)
);

ALTER TABLE users
    DROP COLUMN keywords;
DROP TABLE IF EXISTS keywords;
DROP TABLE IF EXISTS keyword_feedback;
