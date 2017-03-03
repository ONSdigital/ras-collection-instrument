--liquibase formatted sql
--changeset ras_collection_instrument:R1_0_0.ras_collection_instrument_D0001_initial_build.sql

-- R Ingram Initial build 19/02/17

--
-- Schema: ras_collection_instrument, schema for ras_collection_instrument microservice
--
DROP SCHEMA IF EXISTS ras_collection_instrument CASCADE;
CREATE SCHEMA ras_collection_instrument;

--
-- User: ras_collection_instrument, user for ras_collection_instrument microservice
--
DROP USER IF EXISTS ras_collection_instrument;
CREATE USER ras_collection_instrument WITH PASSWORD 'password'
  SUPERUSER INHERIT CREATEDB CREATEROLE NOREPLICATION;

--
-- Table: ras_collection_instruments [COI]
--
DROP TABLE IF EXISTS ras_collection_instrument.ras_collection_instruments;

CREATE TABLE ras_collection_instrument.ras_collection_instruments
(id            BIGSERIAL                NOT NULL
,content       JSONB
,file_uuid     UUID
,created_on    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
,file_path   TEXT 
,CONSTRAINT ras_coi_pk
  PRIMARY KEY (id)
);

--
-- Index: ras_coi_content_idx - to support searhces in the JSON data
--
CREATE INDEX ras_coi_content_idx ON ras_collection_instrument.ras_collection_instruments USING gin(content);

INSERT INTO ras_collection_instrument.ras_collection_instruments
 (content,file_uuid)
VALUES
 ('{"reference":"rsi-fuel",
    "id":"urn:ons.gov.uk:id:ci:001.001.00001",
    "surveyId":"urn:ons.gov.uk:id:survey:001.001.00001",
    "ciType":"ONLINE",
    "classifiers": {"LEGAL_STATUS":"A","INDUSTRY":"B"}
   }'::JSONB
   ,NULL)
,('{"reference":"rsi-fuel",
    "id":"urn:ons.gov.uk:id:ci:001.001.00010",
    "surveyId":"urn:ons.gov.uk:id:survey:001.001.00001",
    "ciType":"ONLINE",
    "classifiers": {"LEGAL_STATUS":"A","INDUSTRY":"B","GEOGRAPHY":"X"}
   }'::JSONB
   ,NULL)
,('{"reference":"rsi-fuel",
    "id":"urn:ons.gov.uk:id:ci:001.001.00011",
    "surveyId":"urn:ons.gov.uk:id:survey:001.001.00002",
    "ciType":"ONLINE",
    "classifiers": {"LEGAL_STATUS":"A","INDUSTRY":"B","GEOGRAPHY":"Y","PHYSICS":"A","CIVIL":"Y"}
   }'::JSONB
   ,NULL)
,('{"reference":"rsi-fuel",
    "id":"urn:ons.gov.uk:id:ci:001.001.00014",
    "surveyId":"urn:ons.gov.uk:id:survey:001.001.00014",
    "ciType":"ONLINE",
    "classifiers": {"LEGAL_STATUS":"A","INDUSTRY":"B","GEOGRAPHY":"Y","PHYSICS":"A","MILITARY":"Y","R&D":"Y","EUROPEAN":"N"}
   }'::JSONB
   ,NULL)
,('{"reference":"rsi-nonfuel",
    "id":"urn:ons.gov.uk:id:ci:001.001.00002",
    "surveyId":"urn:ons.gov.uk:id:survey:001.001.00002",
    "ciType":"OFFLINE",
    "classifiers": {"RU_REF":"01234567890"}
   }'::JSONB
   ,'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');

COMMIT;

--rollback DROP TABLE ras_collection_instrument.ras_collection_instruments;;
