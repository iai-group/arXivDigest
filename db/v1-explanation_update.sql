ALTER TABLE user_recommendations
ADD explanation varchar(1000) not null;

ALTER TABLE system_recommendations
ADD explanation varchar(1000) not null;