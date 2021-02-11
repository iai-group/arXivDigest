CREATE TABLE s2_suggestions(
    s2_id int NOT NULL,
    name varchar(120),
    score int NOT NULL,
    user_id int NOT NULL,
    foreign key (user_id) references users (user_id) on delete cascade,
    primary key (s2_id, user_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;