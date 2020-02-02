create table keywords(
title varchar(500) not null,
keyword varchar(200) not null,
score int not null,
primary key (title, keyword) 
);

CREATE INDEX paper_title_index ON keywords(title);
