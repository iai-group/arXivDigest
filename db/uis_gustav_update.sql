alter table categories
change column category_ID category_id varchar(50) not null;

alter table users
change column user_ID user_id int auto_increment;

alter table user_categories
drop foreign key user_categories_ibfk_1,
change column user_ID user_id int,
add constraint user_categories_ibfk_1_2
foreign key (user_id) references users (user_id)
on delete cascade;

alter table user_categories
drop foreign key user_categories_ibfk_2,
change column category_ID category_id varchar(50),
add constraint user_categories_ibfk_2_2
foreign key (category_id) references category (category_id)
on delete cascade;