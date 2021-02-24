ALTER TABLE users
ADD COLUMN show_semantic_scholar_popup BOOLEAN DEFAULT false AFTER unsubscribe_trace;

CREATE TABLE semantic_scholar_suggestions(
    semantic_scholar_id int NOT NULL,
    name varchar(120),
    score int NOT NULL,
    user_id int NOT NULL,
    created timestamp NOT NULL,
    foreign key (user_id) references users (user_id) on delete cascade,
    primary key (semantic_scholar_id, user_id, created)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE semantic_scholar_suggestion_log(
    user_id int NOT NULL,
    accepted_semantic_scholar_id int NOT NULL,
    foreign key (user_id) references users (user_id) on delete cascade,
    primary key (user_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;