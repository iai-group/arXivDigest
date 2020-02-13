drop table if exists keyword_feedback;

create table keyword_feedback(
user_ID int not null,
keyword varchar(200) not null,
feedback varchar(20) not null,
datestamp date not null,
primary key(user_ID,keyword)
);