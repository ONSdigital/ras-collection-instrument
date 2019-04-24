# Collection Instrument Service API

This page documents the Collection Instrument service API endpoints.

### Encrypt and upload a collection instrument associated to collection exercise and RU

* `POST /collection-instrument-api/1.0.2/upload/<exercise_id>/<RU_id>` (with a file in the data of the POST)

Example Response
```
The upload was successful
```

### Encrypt and upload a collection instrument associated to collection exercise without RU

* `POST /collection-instrument-api/1.0.2/upload/<exercise_id>` (with a file in the data of the POST)

Example Response
```
The upload was successful
```

### Encrypt and upload a collection instrument associated to collection exercise with classifiers

* `POST /collection-instrument-api/1.0.2/upload/<exercise_id>?classifiers={"FORM_TYPE":%20"001"}` (with a file in the data of the POST)

Example Response
```
The upload was successful
```

### upload an eQ collection instrument associated to a survey with classifiers

* `POST /collection-instrument-api/1.0.2/upload?classifiers={"FORM_TYPE":%20"001"}&survey_id=02b9c366-7397-42f7-942a-76dc5876d86d`

Example Response
```
The upload was successful
```

### Link a collection instrument to a collection exercise

* `POST /collection-instrument-api/1.0.2/link-exercise/<instrument_id>/<exercise_id>`

Example Response
```
Linked collection instrument to collection exercise
```

### Unlink a collection instrument from a collection exercise

* `PUT /collection-instrument-api/1.0.2/unlink-exercise/<instrument_id>/<exercise_id>`

Example Response
```
collection instrument and collection exercise unlinked
```

### Find all collection instruments associated with an exercise (CSV)

* `GET /collection-instrument-api/1.0.2/download_csv/<exercise_id>`

Example CSV Response
```csv
"Count","RU Code","Length","Time Stamp"
"1","test_ru_ref","999","2017-10-13 11:25:27.020468"
```

### Download a collection instrument

* `GET /collection-instrument-api/1.0.2/download/<instrument_id>`

Example File Returned
```
adc8dcc1-c35f-4caf-8f5d-93e6287d4872.xlsx
```

### Get the size of a collection instrument

* `GET /collection-instrument-api/1.0.2/instrument_size/<instrument_id>`

Example Response
```
52224
```

### Get count of collection instruments

* `GET /collection-instrument-api/1.0.2/collectioninstrument/count`

Example Response
```
555
```

### Get count of collection instruments by search string

* `GET /collection-instrument-api/1.0.2/collectioninstrument/count?searchString={"COLLECTION_EXERCISE":%20"<exercise_id>"}`

Example Response
```
123
```

### Get collection instrument by search string

* `GET /collection-instrument-api/1.0.2/collectioninstrument?searchString={"form_type":%20"001"}`

Example JSON Response
```json
[{
  "classifiers": {
    "COLLECTION_EXERCISE": [
      "8f078c99-2843-47c6-9c57-13e5966fbc9e"
    ],
    "form_type": "001",
    "RU_REF": [
      "test_ru_ref"
    ]
  },
  "file_name": "file_name",
  "id": "7574283a-d1fd-49df-b684-d7b201e5748a",
  "surveyId": "cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"
}]
```

### Get collection instrument by search string with limit

* `GET /collection-instrument-api/1.0.2/collectioninstrument?searchString={"RU_REF":%20"test_ru_ref"}&limit=1`

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
  "file_name": "file_name",
  "id": "7574283a-d1fd-49df-b684-d7b201e5748a",
  "surveyId": "cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"
}]
```

### Get collection instrument by id

* `GET /collection-instrument-api/1.0.2/collectioninstrument/id/<instrument_id>`

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
  "file_name": "file_name",
  "id": "7574283a-d1fd-49df-b684-d7b201e5748a",
  "surveyId": "cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"
}
```
### Encrypt and upload collection instrument

* `POST /survey_response-api/v1/survey_responses/<case_id>` (with a file in the data of the POST)

Example Response
```
Upload successful
```
