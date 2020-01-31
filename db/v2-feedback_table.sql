create table feedback(
feedback_ID int auto_increment,
user_ID int,
article_ID varchar(50),
type varchar(50) not null,
feedback_text varchar(2500) not null,
foreign key (user_ID) references users (user_ID) on delete cascade,
foreign key (article_ID) references articles(article_ID) on delete cascade,
primary key (feedback_ID)
);
