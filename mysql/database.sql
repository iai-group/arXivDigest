CREATE USER 'restrictedAccess'@'%' IDENTIFIED BY 'pw12@er';
GRANT SELECT,INSERT,UPDATE,DELETE,CREATE ON *.* TO 'restrictedAccess'@'%';
#todo  make constraints better: constraints are somtimes too limiting
drop table if exists systems;
drop table if exists system_recommendations;
drop table if exists user_recommendations; 		
drop table if exists user_files;
drop table if exists user_webpages;
drop table if exists user_categories;
drop table if exists users;

drop table if exists author_affiliations;
drop table  if exists article_categories;
drop table  if exists article_authors;
drop table if exists  authors;
drop table  if exists categories;
drop tables  if exists articles;

create table categories(
category_ID varchar(50) not null,
category varchar(50) not null,
subcategory varchar(50),
category_name varchar(200) not null,
primary key (category_ID)
);

create table users(
user_ID int auto_increment,
email varchar(255) not null unique,
salted_hash char(60) not null,
firstname varchar(255) not null,
lastname varchar(255) not null,
keywords text,
notification_interval int,
last_recommendation_date date default '0-0-0',
registered datetime not null,
admin boolean default false,
primary key (user_ID)		
);

/*  
create table user_files(
userID int,
filename varchar(200) not null,
filedata mediumblob not null,
foreign key (userID) references users (userID) on delete cascade
primary key(userID,filename)
);*/

create table user_webpages(
user_ID int,
url varchar(1000),
foreign key (user_ID) references users (user_ID) on delete cascade,
primary key(user_ID,url)
);
create table user_categories(
user_ID int,
category_ID varchar(50),
foreign key (category_ID) references categories(category_ID) on delete cascade,
foreign key (user_ID) references users (user_ID) on delete cascade,
primary key(user_ID,category_ID)
);

create table articles(
article_ID varchar(50) not null,
title varchar(600) not null,
abstract text not null,
doi varchar(200),
comments text,
license varchar(400),
journal varchar(400),
datestamp date not null,
primary key (article_ID)
);

create table article_categories(
article_ID varchar(50) not null,
category_ID varchar(50) not null,
foreign key (category_ID) references categories(category_ID) on delete cascade,
foreign key (article_ID) references articles(article_ID) on delete cascade,
primary key(article_ID,category_ID)
);

create table article_authors(
author_ID int auto_increment,
article_ID varchar(50) not null,
firstname varchar(200),#not all authors were mentioned with a firstname
lastname varchar(200) not null,
foreign key (article_ID) references articles(article_ID) on delete cascade,
primary key (author_ID) 
);

create table author_affiliations(
author_ID int not null,
affiliation varchar(400) not null,
foreign key (author_ID) references article_authors(author_ID) on delete cascade,
primary key (author_ID,affiliation)
);
create table systems(
system_ID int auto_increment,
api_key char(36) not null unique,
system_name varchar(400) not null unique,
active boolean default true,
primary key(system_ID)
);

create table system_recommendations(
user_ID int,
article_ID varchar(50),
system_ID int,
score float not null,
recommendation_date datetime not null,
foreign key (system_ID) references systems(system_ID) on delete cascade,
foreign key (article_ID) references articles(article_ID) on delete cascade,
foreign key (user_ID) references users (user_ID) on delete cascade,
primary key(user_ID,article_ID,system_ID)
);

create table user_recommendations(
user_ID int,
article_ID varchar(50),
system_ID int,
score int not null,
recommendation_date datetime not null,
seen_email boolean default false,
seen_web boolean default false,
clicked_email boolean default false,
clicked_web boolean default false,
liked boolean default false,
trace_like_email char(36),
trace_click_email char(36),
foreign key (system_ID) references systems(system_ID) on delete cascade,
foreign key (article_ID) references articles(article_ID) on delete cascade,
foreign key (user_ID) references users (user_ID) on delete cascade,
primary key(user_ID,article_ID)
);

DELIMITER $$
CREATE TRIGGER update_last_recommendation_date
AFTER INSERT ON user_recommendations
FOR EACH ROW
BEGIN
  UPDATE users
    SET last_recommendation_date =curdate()
    WHERE user_ID = NEW.user_ID;  -- The OP figured this line out for himself.
END;
$$
DELIMITER ;

#create table articleList(
#ID int auto_increment,
#usersID varchar(100) not null,
#listname varchar(100) not null,
#description varchar(500),
#primary key (ID),
#foreign key (usersID) references users (email) on delete cascade
#);

#create table listItem(
#listID int not null,
#articleID int not null,
#foreign key (listID) references articleList (ID) on delete cascade,
#foreign key (articleID) references articles (ID) on delete cascade
#);

#should find out what indexes we need before creating them
#CREATE INDEX firstNameIndex ON users (firstName);
#CREATE INDEX lastNameIndex ON users (lastName);
#CREATE INDEX interestIndex ON users (interests);
#CREATE INDEX publicationIndex ON users (publicationlist);
#create index tittelIndex on articles (title);
#create index forfatternavnIndex on author (navn);
#create index listeNavnIndex on articleList (navn);