--
-- Script to generate 10000 random-ish CIs for general and performnce testing
-- Please enhance as required.
-- R Ingram 06/03/2017
--
DO $$ DECLARE

  l_ci_urn      TEXT;
  l_survey_urn  TEXT;
  l_classifiers TEXT;
  l_ci_type     TEXT;
  l_chars       TEXT[] := '{A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z}';

BEGIN

  DELETE FROM ras_collection_instrument.ras_collection_instruments;

  FOR i IN 1..10000 LOOP

    -- spread the CIs over 10 surveys
    l_ci_urn     := 'urn:ons.gov.uk:id:ci:001.001.'||LPAD(i::TEXT,5,'0');
    l_survey_urn := 'urn:ons.gov.uk:id:survey:001.001.'||LPAD(MOD(i,10)::TEXT,5,'0');

    -- make every 10th survey an OFFLINE survey
    IF MOD(i,10) = 0 THEN
      l_classifiers := '{"RU_REF":"'||LPAD(i::TEXT,11,'0')||'"}';
      l_ci_type := 'OFFLINE';
    ELSE
      IF MOD(i,3) = 0 THEN
        l_classifiers := '{"LEGAL_STATUS":"'||l_chars[1+random()*(array_length(l_chars,1)-1)]||'",
                           "INDUSTRY":"'||l_chars[1+random()*(array_length(l_chars,1)-1)]||'"}';
      ELSIF MOD(i,3) = 1 THEN
        l_classifiers := '{"GEOGRAPHY":"'||l_chars[1+random()*(array_length(l_chars,1)-1)]||'"}';
      ELSE
        l_classifiers := '{"LEGAL_STATUS":"'||l_chars[1+random()*(array_length(l_chars,1)-1)]||'",
                           "INDUSTRY":"'||l_chars[1+random()*(array_length(l_chars,1)-1)]||'",
                           "GEOGRAPHY":"'||l_chars[1+random()*(array_length(l_chars,1)-1)]||'"}';
      END IF;
      l_ci_type := 'ONLINE';
    END IF;

    INSERT INTO ras_collection_instrument.ras_collection_instruments
      (urn
      ,survey_urn
      ,content
      )
    VALUES
      (l_ci_urn
      ,l_survey_urn
      ,CONCAT('{"id":"',l_ci_urn,'",
                "surveyId":"',l_survey_urn,'",
                "ciType":"',l_ci_type,'",
                "classifiers": ',l_classifiers,'
               }')::JSONB
      );

  END LOOP;

END $$;
