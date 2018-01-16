import base64

from application.controllers.collection_instrument import UPLOAD_SUCCESSFUL
from application.controllers.session_decorator import with_db_session
from application.models.models import ExerciseModel, InstrumentModel, BusinessModel, SurveyModel
from application.views.collection_instrument_view import COLLECTION_INSTRUMENT_NOT_FOUND, NO_INSTRUMENT_FOR_EXERCISE
from flask import current_app
from requests.models import Response
from six import BytesIO
from tests.test_client import TestClient
from unittest.mock import patch
from application.controllers.cryptographer import Cryptographer
from application.exceptions import RasError


class TestCollectionInstrumentView(TestClient):
    """ Collection Instrument view unit tests"""

    def setUp(self):
        self.instrument = self.add_instrument_data()

    def test_collection_instrument_upload(self):
        # Given an upload file and a patched survey_id response
        mock_survey_service = Response()
        mock_survey_service.status_code = 200
        mock_survey_service._content = b'{"surveyId": "cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"}'
        data = {'file': (BytesIO(b'test data'), 'test.xls')}

        with patch('application.controllers.collection_instrument.service_request', return_value=mock_survey_service):
            # When a post is made to the upload end point
            response = self.client.post(
                '/collection-instrument-api/1.0.2/upload/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87'
                '?classifiers={"FORM_TYPE": "001"}',
                headers=self.get_auth_headers(),
                data=data,
                content_type='multipart/form-data')

            # Then the file uploads successfully
            self.assertStatus(response, 200)
            self.assertEquals(response.data.decode(), UPLOAD_SUCCESSFUL)

    def test_collection_instrument_upload_with_ru(self):
        # Given an upload file and a patched survey_id response
        mock_survey_service = Response()
        mock_survey_service.status_code = 200
        mock_survey_service._content = b'{"surveyId": "db0711c3-0ac8-41d3-ae0e-567e5ea1ef87"}'
        data = {'file': (BytesIO(b'test data'), 'test.xls')}

        with patch('application.controllers.collection_instrument.service_request', return_value=mock_survey_service):
            # When a post is made to the upload end point
            response = self.client.post(
                '/collection-instrument-api/1.0.2/upload/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87/9999'
                '?classifiers={"FORM_TYPE": "001"}',
                headers=self.get_auth_headers(),
                data=data,
                content_type='multipart/form-data')

            # Then the file uploads successfully
            self.assertStatus(response, 200)
            self.assertEquals(response.data.decode(), UPLOAD_SUCCESSFUL)

    def test_download_exercise_csv(self):

        # Given a patched exercise
        instrument = InstrumentModel(file_name='file_name', data='test_data', length=999)
        exercise = ExerciseModel(exercise_id='cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87')
        business = BusinessModel(ru_ref='test_ru_ref')
        instrument.exercises.append(exercise)
        instrument.businesses.append(business)

        with patch('application.controllers.collection_instrument.query_exercise_by_id', return_value=exercise):

            # When a call is made to the download_csv end point
            response = self.client.get(
                '/collection-instrument-api/1.0.2/download_csv/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87',
                headers=self.get_auth_headers())

            # Then the response contains the correct data
            self.assertStatus(response, 200)
            self.assertIn('"Count","RU Code","Length","Time Stamp"', response.data.decode())
            self.assertIn('"1","test_ru_ref","999"', response.data.decode())

    def test_get_instrument_by_search_string_ru(self):

        # Given an instrument which is in the db
        # When the collection instrument end point is called with a search string
        response = self.client.get(
            '/collection-instrument-api/1.0.2/collectioninstrument?searchString={"RU_REF":%20"test_ru_ref"}',
            headers=self.get_auth_headers())

        # Then the response returns the correct data
        self.assertStatus(response, 200)
        self.assertIn('test_ru_ref', response.data.decode())
        self.assertIn('cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87', response.data.decode())

    def test_get_instrument_by_search_classifier(self):

        # Given an instrument which is in the db
        # When the collection instrument end point is called with a search classifier
        response = self.client.get(
            '/collection-instrument-api/1.0.2/collectioninstrument?searchString={"FORM_TYPE":%20"001"}',
            headers=self.get_auth_headers())

        # Then the response returns the correct data
        self.assertStatus(response, 200)
        self.assertIn('test_file', response.data.decode())
        self.assertIn('001', response.data.decode())
        self.assertIn('cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87', response.data.decode())

    def test_get_instrument_by_search_multiple_classifiers(self):

        # Given an instrument which is in the db
        # When the collection instrument end point is called with a multiple search classifiers
        response = self.client.get(
            '/collection-instrument-api/1.0.2/collectioninstrument?'
            'searchString={"FORM_TYPE":%20"001","GEOGRAPHY":%20"EN"}',
            headers=self.get_auth_headers())

        # Then the response returns the correct data
        self.assertStatus(response, 200)
        self.assertIn('test_file', response.data.decode())
        self.assertIn('"GEOGRAPHY": "EN"', response.data.decode())
        self.assertIn('"FORM_TYPE": "001"', response.data.decode())
        self.assertIn('cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87', response.data.decode())

    def test_get_instrument_by_search_limit_1(self):

        # Given a 2nd instrument is added
        self.add_instrument_data()
        # When the collection instrument end point is called with limit set to 1
        response = self.client.get(
            '/collection-instrument-api/1.0.2/collectioninstrument?limit=1',
            headers=self.get_auth_headers())

        # Then 1 response is returned
        self.assertStatus(response, 200)
        self.assertIn('test_file', response.data.decode())
        self.assertEquals(response.data.decode().count('cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87'), 1)

    def test_get_instrument_by_search_limit_2(self):

        # Given a 2nd instrument is added
        self.add_instrument_data()
        # When the collection instrument end point is called with limit set to 2
        response = self.client.get(
            '/collection-instrument-api/1.0.2/collectioninstrument?limit=2',
            headers=self.get_auth_headers())

        # Then 2 responses are returned
        self.assertStatus(response, 200)
        self.assertIn('test_ru_ref', response.data.decode())
        self.assertEquals(response.data.decode().count('cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87'), 2)

    def test_get_instrument_by_id(self):

        # Given an instrument which is in the db
        # When the collection instrument end point is called with an id
        response = self.client.get('/collection-instrument-api/1.0.2/collectioninstrument/id/{instrument_id}'
                                   .format(instrument_id=self.instrument), headers=self.get_auth_headers())

        # Then the response returns the correct data
        self.assertStatus(response, 200)
        self.assertIn('test_ru_ref', response.data.decode())
        self.assertIn('cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87', response.data.decode())

    def test_get_instrument_by_id_no_instrument(self):

        # Given a instrument which doesn't exist
        missing_instrument_id = 'ffb8a5e8-03ef-45f0-a85a-3276e98f66b8'

        # When the collection instrument end point is called with an id
        response = self.client.get('/collection-instrument-api/1.0.2/collectioninstrument/id/{instrument_id}'
                                   .format(instrument_id=missing_instrument_id),
                                   headers=self.get_auth_headers())

        # Then the response returns no data
        self.assertStatus(response, 404)
        self.assertEquals(response.data.decode(), COLLECTION_INSTRUMENT_NOT_FOUND)

    def test_download_exercise_csv_missing(self):
        # Given a incorrect exercise id
        # When a call is made to the download_csv end point
        response = self.client.get('/collection-instrument-api/1.0.2/download_csv/d10711c3-0ac8-41d3-ae0e-567e5ea1ef87',
                                   headers=self.get_auth_headers())

        # Then a collection exercise is not found
        self.assertStatus(response, 404)
        self.assertEquals(response.data.decode(), NO_INSTRUMENT_FOR_EXERCISE)

    def test_get_instrument_size(self):

        # Given an instrument which is in the db
        # When the collection instrument size end point is called with an id
        response = self.client.get('/collection-instrument-api/1.0.2/instrument_size/{instrument_id}'
                                   .format(instrument_id=self.instrument), headers=self.get_auth_headers())

        # Then the response returns the correct size
        self.assertStatus(response, 200)
        self.assertIn('999', response.data.decode())

    def test_get_instrument_size_missing_instrument(self):

        # Given an instrument id which doesn't exist in the db
        instrument = '655488ea-ccaa-4d02-8f73-3d20bceed706'

        # When the collection instrument end point is called with an id
        response = self.client.get('/collection-instrument-api/1.0.2/instrument_size/{instrument_id}'
                                   .format(instrument_id=instrument), headers=self.get_auth_headers())

        # Then the response returns a 404
        self.assertStatus(response, 404)

    def test_get_instrument_download(self):

        # Given an instrument which is in the db
        # When the collection instrument end point is called with an id
        response = self.client.get('/collection-instrument-api/1.0.2/download/{instrument_id}'
                                   .format(instrument_id=self.instrument), headers=self.get_auth_headers())

        # Then the response returns the correct instrument
        self.assertStatus(response, 200)
        self.assertIn('test data', response.data.decode())

    def test_get_instrument_download_missing_instrument(self):

        # Given an instrument which doesn't exists in the db
        instrument = '655488ea-ccaa-4d02-8f73-3d20bceed706'

        # When the collection instrument end point is called with an id
        response = self.client.get('/collection-instrument-api/1.0.2/download/{instrument_id}'
                                   .format(instrument_id=instrument), headers=self.get_auth_headers())

        # Then the response returns a 404
        self.assertStatus(response, 404)

    def test_ras_error_in_session(self):
        # Given an upload file and a patched survey_id response which returns a RasError
        data = {'file': (BytesIO(b'test data'), 'test.xls')}
        mock_survey_service = RasError('The service raised an error')

        with patch('application.controllers.collection_instrument.service_request', side_effect=mock_survey_service):
            # When a post is made to the upload end point
            response = self.client.post(
                    '/collection-instrument-api/1.0.2/upload/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87'
                    '?classifiers={"FORM_TYPE": "001"}',
                    headers=self.get_auth_headers(),
                    data=data,
                    content_type='multipart/form-data')

        # Then a error is reported
        self.assertIn('The service raised an error', response.data.decode())

    @staticmethod
    def get_auth_headers():
        auth = "{}:{}".format(current_app.config.get('SECURITY_USER_NAME'),
                              current_app.config.get('SECURITY_USER_PASSWORD')).encode('utf-8')
        return {
            'Authorization': 'Basic %s' % base64.b64encode(bytes(auth)).decode("ascii")
        }

    def test_instrument_by_search_string_ru_missing_auth_details(self):

        # Given an instrument which is in the db
        self.add_instrument_data()
        # When the collection instrument end point is called without auth details
        response = self.client.get(
            '/collection-instrument-api/1.0.2/collectioninstrument?searchString={"RU_REF":%20"test_ru_ref"}')

        # Then a 401 unauthorised is return
        self.assertStatus(response, 401)

    def test_instrument_by_search_string_ru_incorrect_auth_details(self):

        # Given a file and incorrect auth details
        self.add_instrument_data()
        auth = "{}:{}".format('incorrect_user_name', 'incorrect_password').encode('utf-8')
        header = {'Authorization': 'Basic %s' % base64.b64encode(bytes(auth)).decode("ascii")}

        # When the collection instrument end point is called with incorrect auth details
        response = self.client.get(
            '/collection-instrument-api/1.0.2/collectioninstrument?searchString={"RU_REF":%20"test_ru_ref"}',
            headers=header)

        # Then a 401 unauthorised is return
        self.assertStatus(response, 401)

    @staticmethod
    @with_db_session
    def add_instrument_data(session=None):
        instrument = InstrumentModel(file_name='test_file',
                                     classifiers={"FORM_TYPE": "001", "GEOGRAPHY": "EN"},
                                     length='999')
        crypto = Cryptographer()
        data = BytesIO(b'test data')
        instrument.data = crypto.encrypt(data.read())
        exercise = ExerciseModel()
        business = BusinessModel(ru_ref='test_ru_ref')
        instrument.exercises.append(exercise)
        instrument.businesses.append(business)
        survey = SurveyModel(survey_id='cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87')
        instrument.survey = survey
        session.add(instrument)
        return instrument.instrument_id
