create table keyword_opinions(
user_ID int not null,
keyword varchar(200) not null,
opinion varchar(20) not null,
primary key(user_ID,keyword)
);