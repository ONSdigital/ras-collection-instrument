import json
import unittest

from application.app import app, validate_uri, validate_scope, validate_json


class TestApp(unittest.TestCase):
    """
        Unit tests for app.py
    """
    def setUp(self):
        self.app = app.test_client()
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"  # NOQA
        }

    def test_valid_uri(self):
        uri = "urn:ons.gov.uk:id:survey:001.001.00001"
        self.assertEquals(validate_uri(uri, "survey"), True)

    def test_malformed_valid_uri(self):
        # The first element should be urn
        uri = "invalid:ons.gov.uk:id:survey:001.001.00001"
        self.assertEquals(validate_uri(uri, "survey"), False)

    def test_missing_element_valid_uri(self):
        # There are on 4 elements when there should be 5
        uri = "ons.gov.uk:id:survey:001.001.00001"
        self.assertEquals(validate_uri(uri, "survey"), False)

    def test_valid_validate_scope(self):
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmFzLXRlc3QiLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.J5FjerGkmpSWAUKG7_PChUcf5slGON3FNWUkEgMSmRk"  # NOQA
        self.assertEquals(validate_scope(token, "ci.write"), True)

    def test_invalid_validate_scope(self):
        # ci.write is not in the users scope list
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmFzLXRlc3QiLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIl19.tzoqbuT1SJBLLQUHsnG7wBIvpZbxbu9G6Z9M4B9VH4M"  # NOQA
        self.assertEquals(validate_scope(token, "ci.write"), False)

    def test_jwt_error_validate_scope(self):
        token = "invalid"
        self.assertEquals(validate_scope(token, "ci.write"), False)

    def test_key_error_validate_scope(self):
        # user_scopes is missing from JWT
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmFzLXRlc3QifQ.c45jy9chE-jcgh0irk-TbGgicE1z149h1iSC1d47wJk"  # NOQA
        self.assertEquals(validate_scope(token, "ci.write"), False)

    def test_validate_json(self):

        valid_json = {
                "reference": "123",
                "id": "123",
                "ciType": "test",
                "surveyId": "123",
                "classifiers": {
                    "LEGAL_STATUS": "required",
                    "INDUSTRY": "farming",
                    "RU_REF": "23"
                }
            }
        self.assertEquals(validate_json(valid_json), True)

    def test_empty_validate_json(self):
        invalid_json = {}
        self.assertEquals(validate_json(invalid_json), False)

    def test_missing_key_validate_json(self):

        invalid_json = {
            # reference is missing
            "id": "123",
            "ciType": "test",
            "surveyId": "123",
            "classifiers": {
                "LEGAL_STATUS": "required",
                "INDUSTRY": "farming",
                "RU_REF": "23"
            }
        }
        self.assertEquals(validate_json(invalid_json), False)

    def test_get_collection_instrument_id(self):
        response = self.app.get('/collectioninstrument/id/urn:ons.gov.uk:id:ci:001.001.00001', headers=self.headers)
        expected_response = {
                                "reference": "rsi-fuel",
                                "surveyId": "urn:ons.gov.uk:id:survey:001.001.00001",
                                "id": "urn:ons.gov.uk:id:ci:001.001.00001",
                                "ciType": "ONLINE",
                                "classifiers": {
                                    "LEGAL_STATUS": "A",
                                    "INDUSTRY": "B"
                                }
        }
        self.assertEquals(expected_response, json.loads(response.data))

    def test_options_collection_instrument_id_(self):
        expected_response = '{"representation options":["json"]}'
        response = self.app.options('/collectioninstrument/id/urn:ons.gov.uk:id:ci:001.001.00001', headers=self.headers)
        self.assertEquals(expected_response, response.data)

    def test_get_collection_instrument(self):
        response = self.app.get('/collectioninstrument', headers=self.headers)
        expected_response = [{
                'ciType': 'ONLINE',
                'surveyId': 'urn:ons.gov.uk:id:survey:001.001.00001',
                'id': 'urn:ons.gov.uk:id:ci:001.001.00001',
                'reference': 'rsi-fuel',
                'classifiers': {
                    'LEGAL_STATUS': 'A',
                    'INDUSTRY': 'B'
                }
            },
            {
                'ciType': 'ONLINE',
                'surveyId': 'urn:ons.gov.uk:id:survey:001.001.00001',
                'id': 'urn:ons.gov.uk:id:ci:001.001.00010',
                'reference': 'rsi-fuel',
                'classifiers': {
                    'LEGAL_STATUS': 'A',
                    'INDUSTRY': 'B',
                    'GEOGRAPHY': 'X'
                }
            },
            {
                'ciType': 'ONLINE',
                'surveyId': 'urn:ons.gov.uk:id:survey:001.001.00002',
                'id': 'urn:ons.gov.uk:id:ci:001.001.00011',
                'reference': 'rsi-fuel',
                'classifiers': {
                    'CIVIL': 'Y',
                    'LEGAL_STATUS': 'A',
                    'INDUSTRY': 'B',
                    'PHYSICS': 'A',
                    'GEOGRAPHY': 'Y'
                }
            },
            {
                'ciType': 'ONLINE',
                'surveyId': 'urn:ons.gov.uk:id:survey:001.001.00014',
                'id': 'urn:ons.gov.uk:id:ci:001.001.00014',
                'reference': 'rsi-fuel',
                'classifiers': {
                    'INDUSTRY': 'B',
                    'LEGAL_STATUS': 'A',
                    'R&D': 'Y',
                    'MILITARY': 'Y',
                    'GEOGRAPHY': 'Y',
                    'PHYSICS': 'A',
                    'EUROPEAN': 'N'
                }
            },
            {
                'ciType': 'OFFLINE',
                'surveyId': 'urn:ons.gov.uk:id:survey:001.001.00002',
                'id': 'urn:ons.gov.uk:id:ci:001.001.00002',
                'reference': 'rsi-nonfuel',
                'classifiers': {
                    'RU_REF': '01234567890'
                }
            }
        ]
        self.assertEquals(expected_response, json.loads(response.data))

    def test_get_collection_instrument_reference(self):
        response = self.app.get('/collectioninstrument/reference/rsi-fuel', headers=self.headers)
        expected_response = [{
                'ciType': 'ONLINE',
                'surveyId': 'urn:ons.gov.uk:id:survey:001.001.00001',
                'id': 'urn:ons.gov.uk:id:ci:001.001.00001',
                'reference': 'rsi-fuel',
                'classifiers': {
                    'LEGAL_STATUS': 'A',
                    'INDUSTRY': 'B'
                }
            },
            {
                'ciType': 'ONLINE',
                'surveyId': 'urn:ons.gov.uk:id:survey:001.001.00001',
                'id': 'urn:ons.gov.uk:id:ci:001.001.00010',
                'reference': 'rsi-fuel',
                'classifiers': {
                    'LEGAL_STATUS': 'A',
                    'INDUSTRY': 'B',
                    'GEOGRAPHY': 'X'
                }
            },
            {
                'ciType': 'ONLINE',
                'surveyId': 'urn:ons.gov.uk:id:survey:001.001.00002',
                'id': 'urn:ons.gov.uk:id:ci:001.001.00011',
                'reference': 'rsi-fuel',
                'classifiers': {
                    'CIVIL': 'Y',
                    'LEGAL_STATUS': 'A',
                    'INDUSTRY': 'B',
                    'PHYSICS': 'A',
                    'GEOGRAPHY': 'Y'
                }
            },
            {
                'ciType': 'ONLINE',
                'surveyId': 'urn:ons.gov.uk:id:survey:001.001.00014',
                'id': 'urn:ons.gov.uk:id:ci:001.001.00014',
                'reference': 'rsi-fuel',
                'classifiers': {
                    'INDUSTRY': 'B',
                    'LEGAL_STATUS': 'A',
                    'R&D': 'Y',
                    'MILITARY': 'Y',
                    'GEOGRAPHY': 'Y',
                    'PHYSICS': 'A',
                    'EUROPEAN': 'N'
                }
            }]
        self.assertEquals(expected_response, json.loads(response.data))

    def test_get_collection_instrument_survey_id(self):
        response = self.app.get('/collectioninstrument/surveyid/urn:ons.gov.uk:id:survey:001.001.00001?classifier = {"classifiers": {"INDUSTRY": "R", "LEGAL_STATUS": "F", "GEOGRAPHY": "B"}}', headers=self.headers)  # NOQA
        expected_response = [{
                "reference": "rsi-fuel",
                "surveyId": "urn:ons.gov.uk:id:survey:001.001.00001",
                "id": "urn:ons.gov.uk:id:ci:001.001.00010",
                "ciType": "ONLINE",
                "classifiers": {
                    "LEGAL_STATUS": "A",
                    "INDUSTRY": "B",
                    "GEOGRAPHY": "X"
                }
            },
            {
                "reference": "rsi-fuel",
                "surveyId": "urn:ons.gov.uk:id:survey:001.001.00001",
                "id": "urn:ons.gov.uk:id:ci:001.001.00001",
                "ciType": "ONLINE",
                "classifiers": {
                    "LEGAL_STATUS": "A",
                    "INDUSTRY": "B"
                }
            }]
        self.assertEquals(expected_response, json.loads(response.data))
