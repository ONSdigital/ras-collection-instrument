import base64
import json
from unittest.mock import patch

import requests_mock
from flask import current_app
from requests.models import Response
from six import BytesIO

from application.controllers.cryptographer import Cryptographer
from application.controllers.session_decorator import with_db_session
from application.exceptions import RasError
from application.models.models import (BusinessModel, ExerciseModel,
                                       InstrumentModel, SEFTModel, SurveyModel)
from application.views.collection_instrument_view import (
    COLLECTION_INSTRUMENT_NOT_FOUND, NO_INSTRUMENT_FOR_EXERCISE,
    UPLOAD_SUCCESSFUL)
from tests.test_client import TestClient

linked_exercise_id = 'fb2a9d3a-6e9c-46f6-af5e-5f67fec3c040'
url_collection_instrument_link_url = "http://localhost:8145/collection-instrument/link"


@with_db_session
def collection_instruments(session=None):
    return session.query(InstrumentModel).all()


@with_db_session
def collection_exercises(session=None):
    return session.query(ExerciseModel).all()


@with_db_session
def collection_exercises_linked_to_collection_instrument(instrument_id, session=None):
    ci = session.query(InstrumentModel).filter(InstrumentModel.instrument_id == instrument_id).first()
    return ci.exercises


class TestCollectionInstrumentView(TestClient):
    """ Collection Instrument view unit tests"""

    def setUp(self):
        self.instrument_id = self.add_instrument_data()

    @requests_mock.mock()
    def test_collection_instrument_upload(self, mock_request):
        mock_request.post(url_collection_instrument_link_url, status_code=200)
        # Given an upload file and a patched survey_id response
        mock_survey_service = Response()
        mock_survey_service.status_code = 200
        mock_survey_service._content = b'{"surveyId": "cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"}'
        data = {'file': (BytesIO(b'test data'), 'test.xls')}

        with patch('application.controllers.collection_instrument.service_request', return_value=mock_survey_service):
            # When a post is made to the upload end point
            response = self.client.post(
                '/collection-instrument-api/1.0.2/upload/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87'
                '?classifiers={"form_type": "001"}',
                headers=self.get_auth_headers(),
                data=data,
                content_type='multipart/form-data')

        # Then the file uploads successfully
        self.assertStatus(response, 200)
        self.assertEqual(response.data.decode(), UPLOAD_SUCCESSFUL)

        self.assertEqual(len(collection_instruments()), 2)

    def test_upload_collection_instrument_without_collection_exercise(self):
        # When a post is made to the upload end point
        response = self.client.post(
            '/collection-instrument-api/1.0.2/upload?survey_id=cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87',
            headers=self.get_auth_headers(),
            content_type='multipart/form-data')

        # Then CI uploads successfully
        self.assertStatus(response, 200)
        self.assertEqual(response.data.decode(), UPLOAD_SUCCESSFUL)

        self.assertEqual(len(collection_instruments()), 2)

    def test_upload_collection_instrument_without_collection_exercise_duplicate_protection(self):
        # When a post is made to the upload end point
        response = self.client.post(
            '/collection-instrument-api/1.0.2/upload?survey_id=cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87'
            '&classifiers=%7B%22form_type%22%3A%220255%22%2C%22eq_id%22%3A%22rsi%22%7D',
            headers=self.get_auth_headers(),
            content_type='multipart/form-data')

        # Then CI uploads successfully
        self.assertStatus(response, 200)
        self.assertEqual(response.data.decode(), UPLOAD_SUCCESSFUL)

        self.assertEqual(len(collection_instruments()), 2)

        # When a post is made to the upload end point with identical classifiers
        response = self.client.post(
            '/collection-instrument-api/1.0.2/upload?survey_id=cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87'
            '&classifiers=%7B%22form_type%22%3A%220255%22%2C%22eq_id%22%3A%22rsi%22%7D',
            headers=self.get_auth_headers(),
            content_type='multipart/form-data')

        # Then the file upload fails
        error = {
            "errors": ["Cannot upload an instrument with an identical set of classifiers"]
        }
        self.assertStatus(response, 400)
        self.assertEqual(response.json, error)
        self.assertEqual(len(collection_instruments()), 2)

        # When a post is made to the upload end point for the same survey with the same eq_id but different formtype
        response = self.client.post(
            '/collection-instrument-api/1.0.2/upload?survey_id=cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87'
            '&classifiers=%7B%22form_type%22%3A%220266%22%2C%22eq_id%22%3A%22rsi%22%7D',
            headers=self.get_auth_headers(),
            content_type='multipart/form-data')

        # Then CI uploads successfully
        self.assertStatus(response, 200)
        self.assertEqual(response.data.decode(), UPLOAD_SUCCESSFUL)

        self.assertEqual(len(collection_instruments()), 3)

    def test_upload_collection_instrument_if_survey_does_not_exist(self):
        # When a post is made to the upload end point
        response = self.client.post(
            '/collection-instrument-api/1.0.2/upload?survey_id=98b711c3-0ac8-41d3-ae0e-567e5ea1ef87',
            headers=self.get_auth_headers(),
            content_type='multipart/form-data')

        # Then CI uploads successfully
        self.assertStatus(response, 200)
        self.assertEqual(response.data.decode(), UPLOAD_SUCCESSFUL)

        self.assertEqual(len(collection_instruments()), 2)

    @requests_mock.mock()
    def test_collection_instrument_upload_with_ru(self, mock_request):
        mock_request.post(url_collection_instrument_link_url, status_code=200)
        # Given an upload file and a patched survey_id response
        mock_survey_service = Response()
        mock_survey_service.status_code = 200
        mock_survey_service._content = b'{"surveyId": "db0711c3-0ac8-41d3-ae0e-567e5ea1ef87"}'
        data = {'file': (BytesIO(b'test data'), 'test.xls')}

        with patch('application.controllers.collection_instrument.service_request', return_value=mock_survey_service):
            # When a post is made to the upload end point
            response = self.client.post(
                '/collection-instrument-api/1.0.2/upload/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87/9999'
                '?classifiers={"form_type": "001"}',
                headers=self.get_auth_headers(),
                data=data,
                content_type='multipart/form-data')

        # Then the file uploads successfully
        self.assertStatus(response, 200)
        self.assertEqual(response.data.decode(), UPLOAD_SUCCESSFUL)

        self.assertEqual(len(collection_instruments()), 2)

    @requests_mock.mock()
    def test_collection_instrument_upload_with_ru_only_allows_single_one(self, mock_request):
        mock_request.post(url_collection_instrument_link_url, status_code=200)
        """Verify that uploading a collection instrument for a reporting unit twice for the same collection exercise
        will result in an error"""
        # Given an upload file and a patched survey_id response
        mock_survey_service = Response()
        mock_survey_service.status_code = 200
        mock_survey_service._content = b'{"surveyId": "db0711c3-0ac8-41d3-ae0e-567e5ea1ef87"}'
        data = {'file': (BytesIO(b'test data'), '12345678901.xls')}
        data2 = {'file': (BytesIO(b'test data'), '12345678901.xls')}

        with patch('application.controllers.collection_instrument.service_request', return_value=mock_survey_service):
            # When a post is made to the upload end point
            response = self.client.post(
                '/collection-instrument-api/1.0.2/upload/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87/12345678901',
                headers=self.get_auth_headers(), data=data, content_type='multipart/form-data')

            # Then the file uploads successfully
            self.assertStatus(response, 200)
            self.assertEqual(response.data.decode(), UPLOAD_SUCCESSFUL)

            self.assertEqual(len(collection_instruments()), 2)

        with patch('application.controllers.collection_instrument.service_request', return_value=mock_survey_service), \
                patch('pika.BlockingConnection'):
            # When a post is made to the upload end point
            response = self.client.post(
                '/collection-instrument-api/1.0.2/upload/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87/12345678901',
                headers=self.get_auth_headers(), data=data2, content_type='multipart/form-data')

            # Then the file upload fails
            error = {
                "errors": ['Reporting unit 12345678901 already has an instrument uploaded for this collection exercise']
            }
            self.assertStatus(response, 400)
            self.assertEqual(response.json, error)
            self.assertEqual(len(collection_instruments()), 2)

    @requests_mock.mock()
    def test_collection_instrument_upload_with_ru_allowed_for_different_exercises(self, mock_request):
        mock_request.post(url_collection_instrument_link_url, status_code=200)
        """Verify that uploading a collection exercise, bound to a reporting unit, for two separate collection exercises
        results in them both being saved"""
        # Given an upload file and a patched survey_id response
        mock_survey_service = Response()
        mock_survey_service.status_code = 200
        mock_survey_service._content = b'{"surveyId": "db0711c3-0ac8-41d3-ae0e-567e5ea1ef87"}'
        data = {'file': (BytesIO(b'test data'), '12345678901.xls')}
        data2 = {'file': (BytesIO(b'test data'), '12345678901.xls')}

        with patch('application.controllers.collection_instrument.service_request', return_value=mock_survey_service):
            # When a post is made to the upload end point
            response = self.client.post(
                '/collection-instrument-api/1.0.2/upload/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87/12345678901',
                headers=self.get_auth_headers(), data=data, content_type='multipart/form-data')

            # Then the file uploads successfully
            self.assertStatus(response, 200)
            self.assertEqual(response.data.decode(), UPLOAD_SUCCESSFUL)

            self.assertEqual(len(collection_instruments()), 2)

        with patch('application.controllers.collection_instrument.service_request', return_value=mock_survey_service), \
                patch('pika.BlockingConnection'):
            # When a post is made to the upload end point
            response = self.client.post(
                '/collection-instrument-api/1.0.2/upload/5672aa9d-ae54-4cb9-a37b-5ce795522a54/12345678901',
                headers=self.get_auth_headers(), data=data2, content_type='multipart/form-data')

            # Then the file uploads successfully
            self.assertStatus(response, 200)
            self.assertEqual(response.data.decode(), UPLOAD_SUCCESSFUL)

            self.assertEqual(len(collection_instruments()), 3)

    def test_download_exercise_csv(self):
        # Given a patched exercise
        instrument = InstrumentModel()
        seft_file = SEFTModel(instrument_id=instrument.instrument_id, file_name='file_name',
                              data='test_data', length=999)
        instrument.seft_file = seft_file
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
            self.assertIn('"Count","File Name","Length","Time Stamp"', response.data.decode())
            self.assertIn('"1","file_name","999"', response.data.decode())

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

    def test_get_instrument_by_search_string_type(self):
        # Given an instrument which is in the db
        instrument_id = self.add_instrument_without_exercise()

        # When the collection instrument end point is called with a search string
        response = self.client.get(
            '/collection-instrument-api/1.0.2/collectioninstrument?searchString={"TYPE":%20"EQ"}',
            headers=self.get_auth_headers())

        # Then the response returns the correct data
        self.assertStatus(response, 200)
        self.assertIn('cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87', response.data.decode())
        self.assertIn(str(instrument_id), response.data.decode())

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
        self.assertIn('"geography": "EN"', response.data.decode())
        self.assertIn('"form_type": "001"', response.data.decode())
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
        self.assertEqual(response.data.decode().count('cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87'), 1)

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
        self.assertEqual(response.data.decode().count('cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87'), 2)

    def test_count_instrument_by_search_string_ru(self):
        # Given an instrument which is in the db
        # When the collection instrument end point is called with a search string
        response = self.client.get(
            '/collection-instrument-api/1.0.2/collectioninstrument/count?searchString={"RU_REF":%20"test_ru_ref"}',
            headers=self.get_auth_headers())

        # Then the response returns the correct data
        self.assertStatus(response, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data, 1)

    def test_single_count_instrument(self):
        # Given an instrument which is in the db
        # When the collection instrument end point is called with a search string
        response = self.client.get(
            '/collection-instrument-api/1.0.2/collectioninstrument/count',
            headers=self.get_auth_headers())

        # Then the response returns the correct data
        self.assertStatus(response, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data, 1)

    def test_multiple_count_instrument(self):
        # Given a second instrument in the db
        self.add_instrument_data()
        # When the collection instrument end point is called with a search string
        response = self.client.get(
            '/collection-instrument-api/1.0.2/collectioninstrument/count',
            headers=self.get_auth_headers())

        # Then the response returns the correct data
        self.assertStatus(response, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data, 2)

    def test_count_instrument_by_search_classifier(self):
        # Given an instrument which is in the db
        # When the collection instrument end point is called with a search classifier
        response = self.client.get(
            '/collection-instrument-api/1.0.2/collectioninstrument/count?searchString={"FORM_TYPE":%20"001"}',
            headers=self.get_auth_headers())

        # Then the response returns the correct data
        self.assertStatus(response, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data, 1)

    def test_count_instrument_by_search_multiple_classifiers(self):
        # Given an instrument which is in the db
        # When the collection instrument end point is called with a multiple search classifiers
        response = self.client.get(
            '/collection-instrument-api/1.0.2/collectioninstrument/count?'
            'searchString={"FORM_TYPE":%20"001","GEOGRAPHY":%20"EN"}',
            headers=self.get_auth_headers())

        # Then the response returns the correct data
        self.assertStatus(response, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data, 1)

    def test_count_instrument_by_search_multiple_bad_classifiers(self):
        # Given an instrument which is in the db
        # When the collection instrument end point is called with a multiple search classifiers
        response = self.client.get(
            '/collection-instrument-api/1.0.2/collectioninstrument/count?'
            'searchString={"FORM_TYPE":%20"666","GEOGRAPHY":%20"GB"}',
            headers=self.get_auth_headers())

        # Then the response returns the correct data
        self.assertStatus(response, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data, 0)

    def test_get_instrument_by_id(self):
        # Given an instrument which is in the db
        # When the collection instrument end point is called with an id
        response = self.client.get('/collection-instrument-api/1.0.2/collectioninstrument/id/{instrument_id}'
                                   .format(instrument_id=self.instrument_id), headers=self.get_auth_headers())

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
        self.assertEqual(response.data.decode(), COLLECTION_INSTRUMENT_NOT_FOUND)

    def test_download_exercise_csv_missing(self):
        # Given a incorrect exercise id
        # When a call is made to the download_csv end point
        response = self.client.get('/collection-instrument-api/1.0.2/download_csv/d10711c3-0ac8-41d3-ae0e-567e5ea1ef87',
                                   headers=self.get_auth_headers())

        # Then a collection exercise is not found
        self.assertStatus(response, 404)
        self.assertEqual(response.data.decode(), NO_INSTRUMENT_FOR_EXERCISE)

    def test_get_instrument_size(self):
        # Given an instrument which is in the db
        # When the collection instrument size end point is called with an id
        response = self.client.get('/collection-instrument-api/1.0.2/instrument_size/{instrument_id}'
                                   .format(instrument_id=self.instrument_id), headers=self.get_auth_headers())

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
                                   .format(instrument_id=self.instrument_id), headers=self.get_auth_headers())

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
                '?classifiers={"form_type": "001"}',
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

    @requests_mock.mock()
    def test_link_collection_instrument(self, mock_request):
        mock_request.post(url_collection_instrument_link_url, status_code=200)

        # Given an instrument which is in the db is not linked to a collection exercise
        instrument_id = self.add_instrument_without_exercise()
        exercise_id = 'c3c0403a-6e9c-46f6-af5e-5f67fefb2a9d'
        # When the instrument is linked to an exercise
        response = self.client.post(f'/collection-instrument-api/1.0.2/link-exercise/{instrument_id}/{exercise_id}',
                                    headers=self.get_auth_headers())

        # Then that instrument is successfully linked to the given collection exercise
        self.assertStatus(response, 200)
        linked_exercises = collection_exercises_linked_to_collection_instrument(instrument_id)
        linked_exercise_ids = [str(collection_exercise.exercise_id)
                               for collection_exercise in linked_exercises]
        self.assertIn(exercise_id, linked_exercise_ids)

    @requests_mock.mock()
    def test_link_collection_instrument_rest_exception(self, mock_request):
        mock_request.post(url_collection_instrument_link_url, status_code=500)
        # Given an instrument which is in the db is not linked to a collection exercise
        instrument_id = self.add_instrument_without_exercise()
        exercise_id = 'c3c0403a-6e9c-46f6-af5e-5f67fefb2a9d'

        # When the instrument is linked to an exercise
        with self.assertRaises(Exception):
            response = self.client.post(f'/collection-instrument-api/1.0.2/link-exercise/{instrument_id}/{exercise_id}',
                                        headers=self.get_auth_headers())

            response_data = json.loads(response.data)

            self.assertStatus(response, 500)
            self.assertEqual(response_data['errors'][0], 'Failed to publish upload message')

    @requests_mock.mock()
    def test_unlink_collection_instrument(self, mock_request):
        mock_request.post(url_collection_instrument_link_url, status_code=200)
        # Given an instrument which is in the db is linked to a collection exercise

        # When the instrument is unlinked to an exercise
        response = self.client.put(f'/collection-instrument-api/1.0.2/unlink-exercise/'
                                   f'{self.instrument_id}/{linked_exercise_id}',
                                   headers=self.get_auth_headers())

        # Then that instrument and collection exercise are successfully unlinked
        self.assertStatus(response, 200)
        linked_exercises = collection_exercises_linked_to_collection_instrument(self.instrument_id)
        linked_exercise_ids = [str(collection_exercise.exercise_id)
                               for collection_exercise in linked_exercises]
        self.assertNotIn(linked_exercise_id, linked_exercise_ids)

    @requests_mock.mock()
    def test_unlink_collection_instrument_rest_exception(self, mock_request):
        mock_request.post(url_collection_instrument_link_url, status_code=500)
        # Given an instrument which is in the db is linked to a collection exercise

        # When the instrument is unlinked to an exercise but failed to publish messsage
        response = self.client.put(f'/collection-instrument-api/1.0.2/unlink-exercise/'
                                   f'{self.instrument_id}/{linked_exercise_id}', headers=self.get_auth_headers())

        self.assertStatus(response, 500)

    @requests_mock.mock()
    def test_unlink_collection_instrument_does_not_unlink_all_ci_to_given_ce(self, mock_request):
        mock_request.post(url_collection_instrument_link_url, status_code=200)
        # Given there are multiple cis linked to the same ce
        instrument_id = self.add_instrument_without_exercise()

        self.client.post(f'/collection-instrument-api/1.0.2/link-exercise/'
                         f'{instrument_id}/{linked_exercise_id}', headers=self.get_auth_headers())

        # When the instrument is unlinked to an exercise
        with patch('pika.BlockingConnection'):
            response = self.client.put(f'/collection-instrument-api/1.0.2/unlink-exercise/'
                                       f'{self.instrument_id}/{linked_exercise_id}', headers=self.get_auth_headers())

        # Then only that ci and ce are unlinked the other link remains
        self.assertStatus(response, 200)

        linked_exercises = collection_exercises_linked_to_collection_instrument(self.instrument_id)
        linked_exercise_ids = [str(collection_exercise.exercise_id)
                               for collection_exercise in linked_exercises]
        self.assertNotIn(linked_exercise_id, linked_exercise_ids)

        linked_exercises = collection_exercises_linked_to_collection_instrument(instrument_id)
        linked_exercise_ids = [str(collection_exercise.exercise_id)
                               for collection_exercise in linked_exercises]
        self.assertIn(linked_exercise_id, linked_exercise_ids)

    def test_unlink_collection_instrument_not_found_ci(self):
        # given we have an unknown collection instrument id
        unknown_ci = 'c3c0403a-6e9c-46f6-af5e-5f67fefb2a9d'

        # When unlink call made with
        with patch('pika.BlockingConnection'):
            response = self.client.put(f'/collection-instrument-api/1.0.2/unlink-exercise/'
                                       f'{unknown_ci}/{linked_exercise_id}', headers=self.get_auth_headers())

        # Then 404 not found error returned
        response_data = json.loads(response.data)

        self.assertStatus(response, 404)
        self.assertEqual(response_data['errors'][0], 'Unable to find instrument or exercise')

    def test_patch_collection_instrument_empty_file(self):
        # given we have a collection instrument id

        # When patch call made
        data = {'file': (BytesIO(), 'test.xls')}

        response = self.client.patch(f'/collection-instrument-api/1.0.2/{self.instrument_id}',
                                     data=data,
                                     content_type='multipart/form-data',
                                     headers=self.get_auth_headers())

        # Then 400 not found error returned
        response_data = json.loads(response.data)

        self.assertEqual(response_data['errors'][0], 'File is empty')
        self.assertStatus(response, 400)

    def test_patch_collection_instrument_missing_filename(self):
        # given we have a collection instrument id
        instrument_id = 'c3c0403a-6e9c-46f6-af5e-5f67fefb2a9d'

        # When patch call made
        data = {'file': (BytesIO(b'text'), '')}

        response = self.client.patch(f'/collection-instrument-api/1.0.2/{instrument_id}',
                                     data=data,
                                     content_type='multipart/form-data',
                                     headers=self.get_auth_headers())

        # Then 400 not found error returned
        response_data = json.loads(response.data)

        self.assertEqual(response_data['errors'][0], 'Missing filename')
        self.assertStatus(response, 400)

    @staticmethod
    @with_db_session
    def add_instrument_without_exercise(session=None):
        instrument = InstrumentModel(ci_type='EQ', classifiers={"form_type": "001", "geography": "EN"})
        survey = SurveyModel(survey_id='cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87')
        instrument.survey = survey
        business = BusinessModel(ru_ref='test_ru_ref')
        instrument.businesses.append(business)
        session.add(instrument)
        return instrument.instrument_id

    @staticmethod
    @with_db_session
    def add_instrument_data(session=None):
        instrument = InstrumentModel(classifiers={"form_type": "001", "geography": "EN"}, ci_type='SEFT')
        crypto = Cryptographer()
        data = BytesIO(b'test data')
        data = crypto.encrypt(data.read())
        seft_file = SEFTModel(instrument_id=instrument.instrument_id, file_name='test_file', length='999', data=data)
        instrument.seft_file = seft_file
        exercise = ExerciseModel(exercise_id=linked_exercise_id)
        business = BusinessModel(ru_ref='test_ru_ref')
        instrument.exercises.append(exercise)
        instrument.businesses.append(business)
        survey = SurveyModel(survey_id='cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87')
        instrument.survey = survey
        session.add(instrument)
        return instrument.instrument_id
