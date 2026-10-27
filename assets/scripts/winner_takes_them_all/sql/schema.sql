-- Winner Takes Them All: DuckDB schema converted from the MySQL DDL.
-- Execute this file against the target DuckDB database connection.
-- Re-running it creates missing objects without clearing data or resetting IDs;
-- it does not alter existing table definitions.
-- VARCHAR(n) lengths are descriptive only: DuckDB does not enforce them.
-- Sequences start at 1 for a fresh build. Explicitly importing MySQL IDs does
-- not advance them; a migration must align sequences before generating new IDs.

BEGIN TRANSACTION;

CREATE SCHEMA IF NOT EXISTS fbref_scrape;
SET schema = 'fbref_scrape';

-- Dimensions: sequences replace MySQL AUTO_INCREMENT.
CREATE SEQUENCE IF NOT EXISTS seq_player_id START 1 MAXVALUE 4294967295;
CREATE SEQUENCE IF NOT EXISTS seq_team_id START 1 MAXVALUE 4294967295;
CREATE SEQUENCE IF NOT EXISTS seq_comp_id START 1 MAXVALUE 4294967295;
CREATE SEQUENCE IF NOT EXISTS seq_season_id START 1 MAXVALUE 4294967295;

CREATE TABLE IF NOT EXISTS dimplayer (
  player_id   UINTEGER DEFAULT nextval('fbref_scrape.seq_player_id') PRIMARY KEY,
  player_name VARCHAR(120) NOT NULL,
  birth_year  UINTEGER NOT NULL,
  nationality VARCHAR(60),
  position    VARCHAR(10),
  CONSTRAINT uq_player_natural UNIQUE (player_name, birth_year)
);

CREATE TABLE IF NOT EXISTS dimteam (
  team_id   UINTEGER DEFAULT nextval('fbref_scrape.seq_team_id') PRIMARY KEY,
  team_name VARCHAR(120) NOT NULL,
  CONSTRAINT uq_team UNIQUE (team_name)
);

CREATE TABLE IF NOT EXISTS dimcompetition (
  comp_id   UINTEGER DEFAULT nextval('fbref_scrape.seq_comp_id') PRIMARY KEY,
  comp_name VARCHAR(100) NOT NULL,
  CONSTRAINT uq_comp_name UNIQUE (comp_name)
);

CREATE TABLE IF NOT EXISTS dimseason (
  season_id   UINTEGER DEFAULT nextval('fbref_scrape.seq_season_id') PRIMARY KEY,
  season_name VARCHAR(9) NOT NULL,  -- e.g. 2019-2020
  CONSTRAINT uq_season_name UNIQUE (season_name)
);

-- Fact grain: player x team x competition x season.
-- UINTEGER preserves the range of MySQL INT UNSIGNED, including non-negativity.
CREATE TABLE IF NOT EXISTS factplayer (
  player_id UINTEGER NOT NULL,
  team_id   UINTEGER NOT NULL,
  comp_id   UINTEGER NOT NULL,
  season_id UINTEGER NOT NULL,

  matches_played UINTEGER,
  starts         UINTEGER,
  minutes        UINTEGER,

  goals             UINTEGER,
  non_penalty_goals UINTEGER,
  assists           UINTEGER,

  pens_scored    UINTEGER,
  pens_attempted UINTEGER,

  fouls_drawn   UINTEGER,
  offsides      UINTEGER,
  penalties_won UINTEGER,

  xg_expected_goals          DECIMAL(10,3),
  npxg_non_penalty_xg        DECIMAL(10,3),
  xag_expected_assisted_goals DECIMAL(10,3),

  progressive_carries UINTEGER,
  progressive_passes  UINTEGER,

  age UINTEGER,

  PRIMARY KEY (player_id, team_id, comp_id, season_id),

  CONSTRAINT fk_fact_player FOREIGN KEY (player_id) REFERENCES dimplayer(player_id),
  CONSTRAINT fk_fact_team   FOREIGN KEY (team_id)   REFERENCES dimteam(team_id),
  CONSTRAINT fk_fact_comp   FOREIGN KEY (comp_id)   REFERENCES dimcompetition(comp_id),
  CONSTRAINT fk_fact_season FOREIGN KEY (season_id) REFERENCES dimseason(season_id)
);

-- Preserve the existing secondary indexes. Profile analytical queries before
-- adding more: DuckDB also creates indexes for primary, unique and foreign keys.
CREATE INDEX IF NOT EXISTS ix_fact_team ON factplayer(team_id);
CREATE INDEX IF NOT EXISTS ix_fact_comp ON factplayer(comp_id);
CREATE INDEX IF NOT EXISTS ix_fact_season ON factplayer(season_id);
CREATE INDEX IF NOT EXISTS ix_fact_comp_seas ON factplayer(comp_id, season_id);
CREATE INDEX IF NOT EXISTS ix_fact_player_comp_seas ON factplayer(player_id, comp_id, season_id);

-- Staging retains nullable signed integers for raw values before validation.
-- Keep the source column pkwon; map it to factplayer.penalties_won during loading.
CREATE TABLE IF NOT EXISTS factplayer_staging (
  player_name VARCHAR(120),
  birth_year  INTEGER,
  nationality VARCHAR(60),
  position    VARCHAR(10),

  team_name   VARCHAR(120),
  comp_name   VARCHAR(100),
  season_name VARCHAR(9),

  matches_played INTEGER,
  starts         INTEGER,
  minutes        INTEGER,

  goals             INTEGER,
  non_penalty_goals INTEGER,
  assists           INTEGER,

  pens_scored    INTEGER,
  pens_attempted INTEGER,

  fouls_drawn INTEGER,
  offsides    INTEGER,
  pkwon       INTEGER,

  xg_expected_goals          DECIMAL(10,3),
  npxg_non_penalty_xg        DECIMAL(10,3),
  xag_expected_assisted_goals DECIMAL(10,3),

  progressive_carries INTEGER,
  progressive_passes  INTEGER,

  age INTEGER
);

COMMIT;
