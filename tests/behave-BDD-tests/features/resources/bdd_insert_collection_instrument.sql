DELETE FROM ras_collection_instrument.ras_collection_instruments
WHERE urn = 'urn:ons.gov.uk:id:ci:999.999.00000'
AND survey_urn = 'urn:ons.gov.uk:id:survey:999.999.00000';


INSERT INTO ras_collection_instrument.ras_collection_instruments
 (urn,survey_urn,content,file_uuid)
VALUES
 ( 'urn:ons.gov.uk:id:ci:999.999.00000'
  ,'urn:ons.gov.uk:id:survey:999.999.00000'
  ,'{"reference":"test-reference",
    "id":"urn:ons.gov.uk:id:ci:999.999.00000",
    "surveyId":"urn:ons.gov.uk:id:survey:999.999.00000",
    "ciType":"TEST",
    "classifiers": {"TEST_CLASSIFIER":"A"}
   }'::JSONB
   ,'aaaa1111-bb22-cc33-dd44-eeeeee555555')