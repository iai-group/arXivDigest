ALTER TABLE systems
ADD user_ID int default NULL; 

ALTER TABLE systems
ADD FOREIGN KEY (user_ID) REFERENCES users(user_ID);

ALTER TABLE systems
DROP contact_name;

ALTER TABLE systems
DROP organization_name;

ALTER TABLE systems
DROP email;
