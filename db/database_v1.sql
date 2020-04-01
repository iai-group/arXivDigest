CREATE TABLE users(
    user_id                  int auto_increment,
    email                    varchar(60)  NOT NULL UNIQUE,
    salted_hash              char(87)     NOT NULL,
    firstname                varchar(60)  NOT NULL,
    lastname                 varchar(60)  NOT NULL,
    notification_interval    int          NOT NULL,
    last_recommendation_date date         DEFAULT '0000-00-00',
    last_email_date          date         DEFAULT '0000-00-00',
    registered               datetime     NOT NULL,
    admin                    boolean      DEFAULT false,
    organization             varchar(100) NOT NULL,
    dblp_profile             varchar(120) DEFAULT '',
    google_scholar_profile   varchar(120) DEFAULT '',
    semantic_scholar_profile varchar(120) DEFAULT '',
    personal_website         varchar(120) DEFAULT '',
    inactive boolean default true,
    activate_trace char(36) unique default null,
    unsubscribe_trace char(36) unique default null,
    primary key (user_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;


CREATE TABLE systems(
    system_id     int auto_increment,
    api_key       char(36)    NOT NULL UNIQUE,
    system_name   varchar(40) NOT NULL UNIQUE,
    active        boolean     DEFAULT true,
    admin_user_id int         DEFAULT NULL,
    foreign key (admin_user_id) references users (user_id),
    primary key (system_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;


CREATE TABLE categories(
    category_id   varchar(40)  NOT NULL,
    category      varchar(20)  NOT NULL,
    subcategory   varchar(20),
    category_name varchar(200) NOT NULL,
    primary key (category_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;


CREATE TABLE user_categories(
    user_id     int,
    category_id varchar(40),
    foreign key (category_id) references categories (category_id) on delete cascade,
    foreign key (user_id) references users (user_id) on delete cascade,
    primary key (user_id, category_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;


CREATE TABLE articles(
    article_id varchar(20)  NOT NULL,
    title      varchar(300) NOT NULL,
    abstract   text         NOT NULL,
    doi        varchar(200),
    comments   text,
    license    varchar(120),
    journal    varchar(300),
    datestamp  date         NOT NULL,
    primary key (article_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;


CREATE TABLE article_authors(
    author_id  int auto_increment,
    article_id varchar(20) NOT NULL,
    firstname  varchar(60),
    lastname   varchar(60) NOT NULL,
    foreign key (article_id) references articles (article_id) on delete cascade,
    primary key (author_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;


CREATE TABLE author_affiliations(
    author_id   int          NOT NULL,
    affiliation varchar(300) NOT NULL,
    foreign key (author_id) references article_authors (author_id) on delete cascade,
    primary key (author_id, affiliation)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;


CREATE TABLE article_categories(
    article_id  varchar(20) not null,
    category_id varchar(40) not null,
    foreign key (category_id) references categories (category_id) on delete cascade,
    foreign key (article_id) references articles (article_id) on delete cascade,
    primary key (article_id, category_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;


CREATE TABLE article_recommendations(
    user_id             int,
    article_id          varchar(20),
    system_id           int,
    score               float        NOT NULL,
    recommendation_date datetime     NOT NULL,
    explanation         varchar(400) NOT NULL,
    foreign key (system_id) references systems (system_id) on delete cascade,
    foreign key (article_id) references articles (article_id),
    foreign key (user_id) references users (user_id) on delete cascade,
    primary key (user_id, article_id, system_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;


CREATE TABLE article_feedback(
    user_id             int,
    article_id          varchar(20),
    system_id           int,
    score               int          NOT NULL,
    recommendation_date datetime     NOT NULL,
    seen_email          datetime DEFAULT NULL,
    seen_web            datetime DEFAULT NULL,
    clicked_email       datetime DEFAULT NULL,
    clicked_web         datetime DEFAULT NULL,
    saved               datetime DEFAULT NULL,
    trace_save_email    char(36)       UNIQUE,
    trace_click_email   char(36)       UNIQUE,
    explanation         varchar(400) NOT NULL,
    foreign key (system_id) references systems (system_id) on delete cascade,
    foreign key (article_id) references articles (article_id),
    foreign key (user_id) references users (user_id) on delete cascade,
    primary key (user_id, article_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE topics(
    topic_id int auto_increment,
    topic    varchar(50) NOT NULL UNIQUE,
    filtered boolean DEFAULT false,
    primary key (topic_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;


CREATE TABLE user_topics(
    user_id          int                                                                               NOT NULL,
    topic_id         int                                                                               NOT NULL,
    state enum ('USER_ADDED', 'SYSTEM_RECOMMENDED_ACCEPTED', 'SYSTEM_RECOMMENDED_REJECTED', 'REFRESHED', 'EXPIRED', 'USER_REJECTED') NOT NULL,
    interaction_time datetime                                                                          NOT NULL,
    foreign key (user_id) references users (user_id) on delete cascade,
    foreign key (topic_id) references topics (topic_id) on delete cascade,
    primary key (user_id, topic_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;


CREATE TABLE feedback(
     feedback_id     int auto_increment,
     user_id         int,
     article_id      varchar(20),
     type            enum ('Explanation', 'Recommendation', 'Bug', 'Feature', 'Other') NOT NULL,
     feedback_text   varchar(2500)                                                     NOT NULL,
     feedback_values VARCHAR(1000)                                                     NOT NULL DEFAULT '',
     foreign key (user_id) references users (user_id) on delete cascade,
     foreign key (article_id) references articles (article_id) on delete cascade,
     primary key (feedback_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;


CREATE TABLE topic_recommendations(
    user_id            int      NOT NULL,
    topic_id           int      NOT NULL,
    system_id          int      NOT NULL,
    datestamp          datetime NOT NULL,
    system_score       float    NOT NULL,
    interleaving_order int,
    seen               datetime DEFAULT NULL,
    clicked            datetime DEFAULT NULL,
    interleaving_batch datetime default null,
    foreign key (user_id) references users (user_id) on delete cascade,
    foreign key (topic_id) references topics (topic_id) on delete cascade,
    foreign key (system_id) references systems (system_id) on delete cascade,
    primary key (user_id, topic_id, system_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE database_version(
    current_version int not null,
    primary key (current_version)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE INDEX article_date_index on articles (datestamp);
CREATE INDEX user_admin_index on users (admin);
CREATE INDEX recommendation_date_index on article_recommendations (recommendation_date);
CREATE INDEX article_feedback_date_index on article_feedback (recommendation_date);
CREATE INDEX user_topic_state_index on user_topics (state);
CREATE INDEX topic_filtered_index on topics (filtered);
CREATE INDEX topic_date_index on topic_recommendations (datestamp);
CREATE INDEX topic_interleaving_index on topic_recommendations (interleaving_order);

INSERT INTO database_version VALUES (1);
