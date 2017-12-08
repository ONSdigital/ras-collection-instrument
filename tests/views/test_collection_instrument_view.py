import base64

from application.controllers.collection_instrument import UPLOAD_SUCCESSFUL, INVALID_CLASSIFIER
from application.controllers.session_decorator import with_db_session
from application.models.models import ExerciseModel, InstrumentModel, BusinessModel, SurveyModel
from application.views.collection_instrument_view import COLLECTION_INSTRUMENT_NOT_FOUND, NO_INSTRUMENT_FOR_EXERCISE
from flask import current_app
from requests.models import Response
from six import BytesIO
from tests.test_client import TestClient
from unittest.mock import patch
from application.controllers.cryptographer import Cryptographer


class TestCollectionInstrumentView(TestClient):
    """ Collection Instrument view unit tests"""

    def test_collection_instrument_upload(self):
        # Given an upload file and a patched survey_id response
        mock_survey_service = Response()
        mock_survey_service.status_code = 200
        mock_survey_service._content = b'{"surveyId": "cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"}'

        data = dict(file=(BytesIO(b'test data'), 'test.xls'))
        with patch('application.controllers.collection_instrument.service_request', return_value=mock_survey_service):
            # When a post is made to the upload end point
            response = self.client.post(
                '/collection-instrument-api/1.0.2/upload/{ref}/{file}'
                .format(ref='cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87', file='test.xls'),
                headers=self.get_auth_headers(),
                data=data,
                content_type='multipart/form-data')

            # Then the file uploads successfully
            self.assertStatus(response, 200)
            self.assertEquals(response.data.decode(), UPLOAD_SUCCESSFUL)

    def test_download_exercise_csv(self):

        # Given a patched exercise
        instrument = InstrumentModel(data='test_data', length=999)
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
        self.add_instrument_data()
        # When the collection instrument end point is called with a search string
        response = self.client.get(
            '/collection-instrument-api/1.0.2/collectioninstrument?searchString={"RU_REF":%20"test_ru_ref"}',
            headers=self.get_auth_headers())

        # Then the response returns the correct data
        self.assertStatus(response, 200)
        self.assertIn('test_ru_ref', response.data.decode())
        self.assertIn('cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87', response.data.decode())

    def test_get_instrument_by_id(self):

        # Given an instrument which is in the db
        instrument = self.add_instrument_data()
        # When the collection instrument end point is called with an id
        response = self.client.get('/collection-instrument-api/1.0.2/collectioninstrument/id/{instrument_id}'
                                   .format(instrument_id=instrument), headers=self.get_auth_headers())

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
        response = self.client.get('/collection-instrument-api/1.0.2/download_csv/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87',
                                   headers=self.get_auth_headers())

        # Then a collection exercise is not found
        self.assertStatus(response, 404)
        self.assertEquals(response.data.decode(), NO_INSTRUMENT_FOR_EXERCISE)

    def test_get_instrument_size(self):

        # Given an instrument which is in the db
        instrument = self.add_instrument_data()
        # When the collection instrument size end point is called with an id
        response = self.client.get('/collection-instrument-api/1.0.2/instrument_size/{instrument_id}'
                                   .format(instrument_id=instrument), headers=self.get_auth_headers())

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
        instrument = self.add_instrument_data()
        # When the collection instrument end point is called with an id
        response = self.client.get('/collection-instrument-api/1.0.2/download/{instrument_id}'
                                   .format(instrument_id=instrument), headers=self.get_auth_headers())

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

    def test_app_error_handler(self):
        # Given an invalid classifier
        classifier = 'INVALID'
        # When the collection instrument end point is called with a search string
        response = self.client.get(
            '/collection-instrument-api/1.0.2/collectioninstrument?searchString={"'+classifier+'":%20"test_ru_ref"}',
            headers=self.get_auth_headers())

        # Then the response returns a 500 with the correct RasError message
        self.assertStatus(response, 500)
        self.assertIn(INVALID_CLASSIFIER.format(classifier), response.data.decode())

    @staticmethod
    def get_auth_headers():
        auth = "{}:{}".format(current_app.config.get('SECURITY_USER_NAME'),
                              current_app.config.get('SECURITY_USER_PASSWORD')).encode('utf-8')
        return {
            'Authorization': 'Basic %s' % base64.b64encode(bytes(auth)).decode("ascii")
        }

    @staticmethod
    @with_db_session
    def add_instrument_data(session=None):
        instrument = InstrumentModel(length='999')
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
