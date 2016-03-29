DROP DATABASE IF EXISTS stattrack;
CREATE DATABASE  stattrack;
\c stattrack;


DROP TABLE IF EXISTS teams;
CREATE TABLE teams (
  id serial NOT NULL,
  teamname varchar(35)  NOT NULL default '',
  password text NOT NULL default '',
  PRIMARY KEY  (teamname)
) ;

CREATE ROLE tracker with login;
ALTER USER "tracker" WITH PASSWORD 'baseball';
GRANT select, insert, usage ON teams to tracker;
GRANT all ON teams to tracker;
GRANT usage on sequence teams_id_seq to tracker;

create table players (
playerid serial NOT NULL,
firstname varchar (25) NOT NULL default '',
lastname varchar (25) NOT NULL default '',
team varchar(35) references teams(teamname),
hits int NOT NULL default 0,
singles int NOT NULL default 0,
doubles int NOT NULL default 0,
triples int NOT NULL default 0,
homeruns int NOT NULL default 0,
rbi int NOT NULL default 0,
walks int NOT NULL default 0,
flyouts int NOT NULL default 0,
groundouts int NOT NULL default 0,
strikeouts int NOT NULL default 0,
onbyerror int NOT NULL default 0,
runs int NOT NULL default 0,
stolenbases int NOT NULL default 0,
ab int NOT NULL default 0,
pa int NOT NULL default 0,
position varchar(4) NOT NULL default '',
number int NOT NULL default 0,
hitbypitch int NOT NULL default 0,
primary key(playerid) );

GRANT all ON players to tracker;
GRANT usage on sequence players_playerid_seq to tracker;

create table messages (
messageid serial NOT NULL,
author varchar (35) references teams(teamname),
message text NOT NULL default '',
primary key(messageid) );

GRANT all ON messages to tracker;
GRANT usage on sequence messages_messageid_seq to tracker;