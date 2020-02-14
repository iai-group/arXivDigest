create table keywords(
keyword_ID int auto_increment,
title varchar(3000) not null,
keyword varchar(200) not null,
score int not null,
primary key (keyword_ID)
);

CREATE INDEX paper_title_index ON keywords(title(500));
