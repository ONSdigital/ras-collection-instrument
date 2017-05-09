import unittest


from application.app import validate_uri, validate_scope, validate_json


class TestApplication(unittest.TestCase):

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
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmFzLXRlc3QiLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.J5FjerGkmpSWAUKG7_PChUcf5slGON3FNWUkEgMSmRk" # NOQA
        self.assertEquals(validate_scope(token, "ci.write"), True)

    def test_invalid_validate_scope(self):
        # ci.write is not in the users scope list
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmFzLXRlc3QiLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIl19.tzoqbuT1SJBLLQUHsnG7wBIvpZbxbu9G6Z9M4B9VH4M" # NOQA
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