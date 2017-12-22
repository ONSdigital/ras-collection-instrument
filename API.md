# Collection Instrument Service API

This page documents the Collection Instrument service API endpoints.

### Encrypt and upload a collection exercise

* `POST /collection-instrument-api/1.0.2/upload/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87/test.xls` (with a file in the data of the POST)

Example Response
```
The upload was successful
```

### Find all collection instruments associated with an exercise (CSV)

* `GET /collection-instrument-api/1.0.2/download_csv/8f078c99-2843-47c6-9c57-13e5966fbc9e`

Example CSV Response
```csv
"Count","RU Code","Length","Time Stamp"
"1","test_ru_ref","999","2017-10-13 11:25:27.020468"
```

### Download a collection instrument

* `GET /collection-instrument-api/1.0.2/download/adc8dcc1-c35f-4caf-8f5d-93e6287d4872`

Example File Returned
```
adc8dcc1-c35f-4caf-8f5d-93e6287d4872.xlsx
```

### Get the size of a collection instrument

* `GET /collection-instrument-api/1.0.2/instrument_size/adc8dcc1-c35f-4caf-8f5d-93e6287d4872`

Example Response
```
52224
```

### Get collection instrument by search string

* `GET /collection-instrument-api/1.0.2/collectioninstrument?searchString={"RU_REF":%20"test_ru_ref"}`

Example JSON Response
```json
[{
  "classifiers": {
    "COLLECTION_EXERCISE": [
      "8f078c99-2843-47c6-9c57-13e5966fbc9e"
    ],
    "RU_REF": [
      "test_ru_ref"
    ]
  },
  "id": "7574283a-d1fd-49df-b684-d7b201e5748a",
  "surveyId": "cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"
}]
```
### Get collection instrument by id

* `GET /collection-instrument-api/1.0.2/collectioninstrument/id/7574283a-d1fd-49df-b684-d7b201e5748a`

Example JSON Response
```json
{
  "classifiers": {
    "COLLECTION_EXERCISE": [
      "8f078c99-2843-47c6-9c57-13e5966fbc9e"
    ],
    "RU_REF": [
      "test_ru_ref"
    ]
  },
  "id": "7574283a-d1fd-49df-b684-d7b201e5748a",
  "surveyId": "cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"
}
```
### Encrypt and upload collection instrument

* `POST /survey_response-api/v1/survey_responses/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87` (with a file in the data of the POST)

Example Response
```
Upload successful
```