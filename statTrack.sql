DROP DATABASE IF EXISTS stattrack;
CREATE DATABASE  stattrack;
\c stattrack;


DROP TABLE IF EXISTS teams;
CREATE TABLE teams (
  id serial NOT NULL,
  teamname varchar(35)  NOT NULL default '',
  password text NOT NULL default '',
  PRIMARY KEY  (id)
) ;

CREATE ROLE tracker with login;
ALTER USER "tracker" WITH PASSWORD 'baseball';
GRANT select, insert, usage ON teams to tracker;
GRANT all ON teams to tracker;