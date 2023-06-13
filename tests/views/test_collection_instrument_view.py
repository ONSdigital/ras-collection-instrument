import base64
import json
from unittest import mock
from unittest.mock import patch

import requests_mock
from flask import current_app
from requests.models import Response
from six import BytesIO

from application.controllers.collection_instrument import (
    COLLECTION_EXERCISE_AND_ASSOCIATED_FILES_DELETED,
)
from application.controllers.session_decorator import with_db_session
from application.exceptions import RasError
from application.models.models import (
    BusinessModel,
    ExerciseModel,
    InstrumentModel,
    SEFTModel,
    SurveyModel,
)
from application.views.collection_instrument_view import (
    COLLECTION_INSTRUMENT_DELETED_SUCCESSFUL,
    COLLECTION_INSTRUMENT_NOT_FOUND,
    NO_INSTRUMENT_FOR_EXERCISE,
    UPLOAD_SUCCESSFUL,
)
from tests.test_client import TestClient

linked_exercise_id = "fb2a9d3a-6e9c-46f6-af5e-5f67fec3c040"
url_collection_instrument_link_url = "http://localhost:8145/collection-instrument/link"
survey_url = "http://localhost:8080/surveys/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"
survey_response_json = {"surveyId": "cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87", "surveyRef": "139", "surveyMode": "SEFT"}
collection_exercise_url = "http://localhost:8145/collectionexercises/6790cdaa-28a9-4429-905c-0e943373b62e"

survey_response_json_EQ_AND_SEFT = {
    "surveyId": "cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87",
    "surveyRef": "139",
    "surveyMode": "EQ_AND_SEFT",
}


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


@with_db_session
def collection_exercises_and_collection_instrument(exercise_id, session=None):
    ce = session.query(ExerciseModel).filter(ExerciseModel.exercise_id == exercise_id).first()
    return ce.instruments, ce.exercise_id


class TestCollectionInstrumentView(TestClient):
    """Collection Instrument view unit tests"""

    def setUp(self):
        self.instrument_id = self.add_instrument_data()

    @mock.patch("application.controllers.collection_instrument.GoogleCloudSEFTCIBucket")
    @requests_mock.mock()
    def test_upload_seft_collection_instrument(self, mock_bucket, mock_request):
        mock_request.post(url_collection_instrument_link_url, status_code=200)
        mock_request.get(survey_url, status_code=200, json=survey_response_json)
        mock_bucket.return_value.upload_file_to_bucket.return_value = "file_path.xlsx"
        # Given an upload file and a patched survey_id response
        mock_survey_service = Response()
        mock_survey_service.status_code = 200
        mock_survey_service._content = b'{"surveyId": "cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"}'
        data = {"file": (BytesIO(b"test data"), "test.xls")}

        with patch("application.controllers.collection_instrument.service_request", return_value=mock_survey_service):
            # When a post is made to the upload end point
            response = self.client.post(
                "/collection-instrument-api/1.0.2/upload/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"
                '?classifiers={"form_type": "001"}',
                headers=self.get_auth_headers(),
                data=data,
                content_type="multipart/form-data",
            )

        # Then the file uploads successfully
        self.assertStatus(response, 200)
        self.assertEqual(response.data.decode(), UPLOAD_SUCCESSFUL)

        self.assertEqual(len(collection_instruments()), 2)

    @requests_mock.mock()
    def test_upload_eq_collection_instrument(self, mock_request):
        # When a post is made to the upload end point
        mock_request.get(survey_url, status_code=200, json=survey_response_json)
        response = self.client.post(
            "/collection-instrument-api/1.0.2/upload?survey_id=cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87",
            headers=self.get_auth_headers(),
            content_type="multipart/form-data",
        )

        # Then CI uploads successfully
        self.assertStatus(response, 200)
        self.assertEqual(response.data.decode(), UPLOAD_SUCCESSFUL)

        self.assertEqual(len(collection_instruments()), 2)

    @requests_mock.mock()
    def test_upload_eq_collection_instrument_duplicate_protection(self, mock_request):
        # When a post is made to the upload end point
        mock_request.get(survey_url, status_code=200, json=survey_response_json)
        response = self.client.post(
            "/collection-instrument-api/1.0.2/upload?survey_id=cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"
            "&classifiers=%7B%22form_type%22%3A%220255%22%2C%22eq_id%22%3A%22rsi%22%7D",
            headers=self.get_auth_headers(),
            content_type="multipart/form-data",
        )

        # Then CI uploads successfully
        self.assertStatus(response, 200)
        self.assertEqual(response.data.decode(), UPLOAD_SUCCESSFUL)

        self.assertEqual(len(collection_instruments()), 2)

        # When a post is made to the upload end point with identical classifiers
        response = self.client.post(
            "/collection-instrument-api/1.0.2/upload?survey_id=cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"
            "&classifiers=%7B%22form_type%22%3A%220255%22%2C%22eq_id%22%3A%22rsi%22%7D",
            headers=self.get_auth_headers(),
            content_type="multipart/form-data",
        )

        # Then the file upload fails
        error = {"errors": ["Cannot upload an instrument with an identical set of classifiers"]}
        self.assertStatus(response, 400)
        self.assertEqual(response.json, error)
        self.assertEqual(len(collection_instruments()), 2)

        # When a post is made to the upload end point for the same survey with the same eq_id but different formtype
        response = self.client.post(
            "/collection-instrument-api/1.0.2/upload?survey_id=cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"
            "&classifiers=%7B%22form_type%22%3A%220266%22%2C%22eq_id%22%3A%22rsi%22%7D",
            headers=self.get_auth_headers(),
            content_type="multipart/form-data",
        )

        # Then CI uploads successfully
        self.assertStatus(response, 200)
        self.assertEqual(response.data.decode(), UPLOAD_SUCCESSFUL)

        self.assertEqual(len(collection_instruments()), 3)

    @requests_mock.mock()
    def test_upload_eq_collection_instrument_if_survey_does_not_exist(self, mock_request):
        mock_request.get(survey_url, status_code=200, json=survey_response_json)
        # When a post is made to the upload end point
        response = self.client.post(
            "/collection-instrument-api/1.0.2/upload?survey_id=cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87",
            headers=self.get_auth_headers(),
            content_type="multipart/form-data",
        )

        # Then CI uploads successfully
        self.assertStatus(response, 200)
        self.assertEqual(response.data.decode(), UPLOAD_SUCCESSFUL)

        self.assertEqual(len(collection_instruments()), 2)

    @mock.patch("application.controllers.collection_instrument.GoogleCloudSEFTCIBucket")
    @requests_mock.mock()
    def test_upload_seft_collection_instrument_with_ru(self, mock_bucket, mock_request):
        mock_request.post(url_collection_instrument_link_url, status_code=200)
        mock_request.get(survey_url, status_code=200, json=survey_response_json)
        mock_bucket.return_value.upload_file_to_bucket.return_value = "file_path.xlsx"
        # Given an upload file and a patched survey_id response
        mock_survey_service = Response()
        mock_survey_service.status_code = 200
        mock_survey_service._content = b'{"surveyId": "cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"}'
        data = {"file": (BytesIO(b"test data"), "test.xls")}

        with patch("application.controllers.collection_instrument.service_request", return_value=mock_survey_service):
            # When a post is made to the upload end point
            response = self.client.post(
                "/collection-instrument-api/1.0.2/upload/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87/9999"
                '?classifiers={"form_type": "001"}',
                headers=self.get_auth_headers(),
                data=data,
                content_type="multipart/form-data",
            )

        # Then the file uploads successfully
        self.assertStatus(response, 200)
        self.assertEqual(response.data.decode(), UPLOAD_SUCCESSFUL)

        self.assertEqual(len(collection_instruments()), 2)

    @mock.patch("application.controllers.collection_instrument.GoogleCloudSEFTCIBucket")
    @requests_mock.mock()
    def test_upload_seft_collection_instrument_with_ru_only_allows_single_one(self, mock_bucket, mock_request):
        mock_request.post(url_collection_instrument_link_url, status_code=200)
        mock_request.get(survey_url, status_code=200, json=survey_response_json)
        mock_bucket.return_value.upload_file_to_bucket.return_value = "file_path.xlsx"
        """Verify that uploading a collection instrument for a reporting unit twice for the same collection exercise
        will result in an error"""
        # Given an upload file and a patched survey_id response
        mock_survey_service = Response()
        mock_survey_service.status_code = 200
        mock_survey_service._content = b'{"surveyId": "cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"}'
        data = {"file": (BytesIO(b"test data"), "12345678901.xls")}
        data2 = {"file": (BytesIO(b"test data"), "12345678900.xls")}

        with patch("application.controllers.collection_instrument.service_request", return_value=mock_survey_service):
            # When a post is made to the upload end point
            response = self.client.post(
                "/collection-instrument-api/1.0.2/upload/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87/12345678901",
                headers=self.get_auth_headers(),
                data=data,
                content_type="multipart/form-data",
            )

            # Then the file uploads successfully
            self.assertStatus(response, 200)
            self.assertEqual(response.data.decode(), UPLOAD_SUCCESSFUL)

            self.assertEqual(len(collection_instruments()), 2)

        with patch("application.controllers.collection_instrument.service_request", return_value=mock_survey_service):
            # When a post is made to the upload end point
            response = self.client.post(
                "/collection-instrument-api/1.0.2/upload/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87/12345678901",
                headers=self.get_auth_headers(),
                data=data2,
                content_type="multipart/form-data",
            )

            # Then the file upload fails
            error = {
                "errors": ["Reporting unit 12345678901 already has an instrument uploaded for this collection exercise"]
            }
            self.assertStatus(response, 400)
            self.assertEqual(response.json, error)
            self.assertEqual(len(collection_instruments()), 2)

    @mock.patch("application.controllers.collection_instrument.GoogleCloudSEFTCIBucket")
    @requests_mock.mock()
    def test_upload_seft_collection_instrument_with_duplicate_filename_causes_error(self, mock_bucket, mock_request):
        mock_request.get(survey_url, status_code=200, json=survey_response_json)
        mock_request.post(url_collection_instrument_link_url, status_code=200)
        mock_bucket.return_value.upload_file_to_bucket.return_value = "file_path.xlsx"
        """Verify that uploading a collection instrument file that has the same name as a file already uploaded
        for that collection exercise results in an error"""
        # Given an upload file and a patched survey_id response
        mock_survey_service = Response()
        mock_survey_service.status_code = 200
        mock_survey_service._content = b'{"surveyId": "cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"}'
        data = {"file": (BytesIO(b"test data"), "12345678901.xls")}
        data2 = {"file": (BytesIO(b"test data"), "12345678901.xls")}

        with patch("application.controllers.collection_instrument.service_request", return_value=mock_survey_service):
            # When a post is made to the upload end point
            response = self.client.post(
                "/collection-instrument-api/1.0.2/upload/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87/12345678901",
                headers=self.get_auth_headers(),
                data=data,
                content_type="multipart/form-data",
            )

            # Then the file uploads successfully
            self.assertStatus(response, 200)
            self.assertEqual(response.data.decode(), UPLOAD_SUCCESSFUL)

            self.assertEqual(len(collection_instruments()), 2)

        with patch("application.controllers.collection_instrument.service_request", return_value=mock_survey_service):
            # When a post is made to the upload end point
            response = self.client.post(
                "/collection-instrument-api/1.0.2/upload/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87/12345678901",
                headers=self.get_auth_headers(),
                data=data2,
                content_type="multipart/form-data",
            )

            # Then the file upload fails
            error = {"errors": ["Collection instrument file already uploaded for this collection exercise"]}
            self.assertStatus(response, 400)
            self.assertEqual(response.json, error)
            self.assertEqual(len(collection_instruments()), 2)

    @mock.patch("application.controllers.collection_instrument.GoogleCloudSEFTCIBucket")
    @requests_mock.mock()
    def test_upload_seft_collection_instrument_with_ru_allowed_for_different_exercises(self, mock_bucket, mock_request):
        mock_request.post(url_collection_instrument_link_url, status_code=200)
        mock_request.get(survey_url, status_code=200, json=survey_response_json)
        mock_bucket.return_value.upload_file_to_bucket.return_value = "file_path.xlsx"
        """Verify that uploading a collection exercise, bound to a reporting unit, for two separate collection exercises
        results in them both being saved"""
        # Given an upload file and a patched survey_id response
        mock_survey_service = Response()
        mock_survey_service.status_code = 200
        mock_survey_service._content = b'{"surveyId": "cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"}'
        data = {"file": (BytesIO(b"test data"), "12345678901.xls")}
        data2 = {"file": (BytesIO(b"test data"), "12345678901.xls")}

        with patch("application.controllers.collection_instrument.service_request", return_value=mock_survey_service):
            # When a post is made to the upload end point
            response = self.client.post(
                "/collection-instrument-api/1.0.2/upload/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87/12345678901",
                headers=self.get_auth_headers(),
                data=data,
                content_type="multipart/form-data",
            )

            # Then the file uploads successfully
            self.assertStatus(response, 200)
            self.assertEqual(response.data.decode(), UPLOAD_SUCCESSFUL)

            self.assertEqual(len(collection_instruments()), 2)

        with patch("application.controllers.collection_instrument.service_request", return_value=mock_survey_service):
            # When a post is made to the upload end point
            response = self.client.post(
                "/collection-instrument-api/1.0.2/upload/5672aa9d-ae54-4cb9-a37b-5ce795522a54/12345678901",
                headers=self.get_auth_headers(),
                data=data2,
                content_type="multipart/form-data",
            )

            # Then the file uploads successfully
            self.assertStatus(response, 200)
            self.assertEqual(response.data.decode(), UPLOAD_SUCCESSFUL)

            self.assertEqual(len(collection_instruments()), 3)

    @requests_mock.mock()
    def test_upload_eq_collection_instrument_eq_and_seft_survey_mode(self, mock_request):
        # Given a survey with mode EQ_AND_SEFT
        mock_request.get(survey_url, status_code=200, json=survey_response_json_EQ_AND_SEFT)

        # When a eQ collection instrument is uploaded
        response = self.client.post(
            "/collection-instrument-api/1.0.2/upload?survey_id=cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87",
            headers=self.get_auth_headers(),
            content_type="multipart/form-data",
        )

        # Then the file uploads successfully
        self.assertStatus(response, 200)
        self.assertEqual(response.data.decode(), UPLOAD_SUCCESSFUL)

    @mock.patch("application.controllers.collection_instrument.GoogleCloudSEFTCIBucket")
    @requests_mock.mock()
    def test_upload_seft_collection_instrument_eq_and_seft_survey_mode(self, mock_bucket, mock_request):
        # Given a survey with mode EQ_AND_SEFT
        mock_request.post(url_collection_instrument_link_url, status_code=200)
        mock_request.get(survey_url, status_code=200, json=survey_response_json_EQ_AND_SEFT)
        mock_bucket.return_value.upload_file_to_bucket.return_value = "file_path.xlsx"
        mock_survey_service = Response()
        mock_survey_service.status_code = 200
        mock_survey_service._content = b'{"surveyId": "cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"}'
        data = {"file": (BytesIO(b"test data"), "test.xls")}

        # When a SEFT collection instrument is uploaded
        with patch("application.controllers.collection_instrument.service_request", return_value=mock_survey_service):
            response = self.client.post(
                "/collection-instrument-api/1.0.2/upload/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"
                '?classifiers={"form_type": "001"}',
                headers=self.get_auth_headers(),
                data=data,
                content_type="multipart/form-data",
            )

        # Then the file uploads successfully
        self.assertStatus(response, 200)
        self.assertEqual(response.data.decode(), UPLOAD_SUCCESSFUL)

    @requests_mock.mock()
    def test_upload_eq_collection_instrument_eq_and_seft_survey_mode_form_type_used(self, mock_request):
        # Given a survey with mode EQ_AND_SEFT
        mock_request.get(survey_url, status_code=200, json=survey_response_json_EQ_AND_SEFT)
        self.add_instrument_data()

        # When an eQ collection instrument is uploaded with a form_type already used by a SEFT collection instrument
        response = self.client.post(
            "/collection-instrument-api/1.0.2/upload?survey_id=cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"
            '&classifiers={"form_type": "001"}',
            headers=self.get_auth_headers(),
            content_type="multipart/form-data",
        )

        # Then the file does not upload and an 400 error is returned
        error = {"errors": ["This form type is currently being used by SEFT for this survey"]}
        self.assertStatus(response, 400)
        self.assertEqual(response.json, error)

    @requests_mock.mock()
    def test_upload_seft_collection_instrument_eq_and_seft_survey_mode_form_type_used(self, mock_request):
        # Given a survey with mode EQ_AND_SEFT
        mock_request.get(survey_url, status_code=200, json=survey_response_json_EQ_AND_SEFT)
        mock_request.get(
            collection_exercise_url, status_code=200, json={"surveyId": "cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"}
        )

        data = {"file": (BytesIO(b"test data"), "test.xls")}
        self.add_instrument_data(ci_type="EQ")

        # When a SEFT collection instrument is uploaded with a form_type already used by an eQ collection instrument
        response = self.client.post(
            "/collection-instrument-api/1.0.2/upload/6790cdaa-28a9-4429-905c-0e943373b62e"
            '?classifiers={"form_type": "001"}',
            headers=self.get_auth_headers(),
            data=data,
            content_type="multipart/form-data",
        )

        # Then the file does not upload and an 400 error is returned
        error = {"errors": ["This form type is currently being used by EQ for this survey"]}
        self.assertStatus(response, 400)
        self.assertEqual(response.json, error)

    @requests_mock.mock()
    def test_upload_no_ru_ref_instrument_for_eq_and_seft(self, mock_request):
        mock_request.get(survey_url, status_code=200, json=survey_response_json_EQ_AND_SEFT)
        mock_request.get(
            collection_exercise_url, status_code=200, json={"surveyId": "cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"}
        )
        # Given an upload file
        data = {"file": (BytesIO(b"test data"), "test.xls")}

        # When a post is made to the ru specific upload endpoint
        response = self.client.post(
            "/collection-instrument-api/1.0.2/upload/6790cdaa-28a9-4429-905c-0e943373b62e/49990000001",
            headers=self.get_auth_headers(),
            data=data,
            content_type="multipart/form-data",
        )

        # Then the file does not upload and an 400 error is returned
        error = {"errors": ["Can't upload a reporting unit specific instrument for an EQ_AND_SEFT survey"]}
        self.assertStatus(response, 400)
        self.assertEqual(response.json, error)

    @mock.patch("application.controllers.collection_instrument.GoogleCloudSEFTCIBucket")
    @requests_mock.mock()
    def test_delete_seft_collection_instrument(self, mock_bucket, mock_request):
        # Given an collection instrument and GCS is patched
        mock_request.get(survey_url, status_code=200, json=survey_response_json)
        mock_bucket.delete_file_from_bucket.return_value = True

        # When a post is made to delete the instrument
        response = self.client.delete(
            f"/collection-instrument-api/1.0.2/delete/{self.instrument_id}",
            headers=self.get_auth_headers(),
            content_type="multipart/form-data",
        )

        # Then the instrument is deleted successfully
        self.assertStatus(response, 200)
        self.assertEqual(response.data.decode(), COLLECTION_INSTRUMENT_DELETED_SUCCESSFUL)

    @mock.patch(
        "application.controllers.collection_instrument.CollectionInstrument.delete_collection_instruments_by_exercise"
    )
    def test_delete_collection_instrument_by_exercise(self, delete_collection_instruments_by_exercise):
        # Given delete_collection_instruments_by_exercise is mocked to return a successful deletion
        delete_collection_instruments_by_exercise.return_value = COLLECTION_EXERCISE_AND_ASSOCIATED_FILES_DELETED, 200

        # When delete_collection_instruments_by_exercise is called
        response = self.client.delete(
            "/collection-instrument-api/1.0.2/delete/collection-exercise/fb2a9d3a-6e9c-46f6-af5e-5f67fec3c040",
            headers=self.get_auth_headers(),
            content_type="multipart/form-data",
        )

        # Then the response is as expected
        self.assertStatus(response, 200)
        self.assertEqual(response.data.decode(), COLLECTION_EXERCISE_AND_ASSOCIATED_FILES_DELETED)

    def test_delete_eq_collection_instrument(self):
        eq_collection_instrument_id = self.add_instrument_data(ci_type="EQ")
        # When a post is made to delete the instrument
        response = self.client.delete(
            f"/collection-instrument-api/1.0.2/delete/{str(eq_collection_instrument_id)}",
            headers=self.get_auth_headers(),
            content_type="multipart/form-data",
        )

        # Then the instrument is deleted successfully
        self.assertStatus(response, 200)
        self.assertEqual(response.data.decode(), COLLECTION_INSTRUMENT_DELETED_SUCCESSFUL)

    @mock.patch("application.controllers.collection_instrument.GoogleCloudSEFTCIBucket")
    @requests_mock.mock()
    def test_download_seft_exercise_csv(self, mock_bucket, mock_request):
        # Given a patched exercise
        instrument = InstrumentModel()
        seft_file = SEFTModel(instrument_id=instrument.instrument_id, file_name="file_name", data="test_data", length=6)
        survey = SurveyModel()
        survey.survey_id = "cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"
        instrument.survey = survey
        instrument.seft_file = seft_file
        exercise = ExerciseModel(exercise_id="cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87")
        business = BusinessModel(ru_ref="test_ru_ref")
        instrument.exercises.append(exercise)
        instrument.businesses.append(business)

        mock_bucket.return_value.download_file_from_bucket.return_value = "abc123"
        mock_request.get(survey_url, status_code=200, json=survey_response_json)

        with patch("application.controllers.collection_instrument.query_exercise_by_id", return_value=exercise):
            # When a call is made to the download_csv end point
            response = self.client.get(
                "/collection-instrument-api/1.0.2/download_csv/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87",
                headers=self.get_auth_headers(),
            )

            # Then the response contains the correct data
            self.assertStatus(response, 200)
            self.assertIn('"Count","File Name","Length","Time Stamp"', response.data.decode())
            self.assertIn('"1","file_name","6"', response.data.decode())

    def test_get_instrument_by_search_string_ru(self):
        # Given an instrument which is in the db
        # When the collection instrument end point is called with a search string
        response = self.client.get(
            '/collection-instrument-api/1.0.2/collectioninstrument?searchString={"RU_REF":%20"test_ru_ref"}',
            headers=self.get_auth_headers(),
        )

        # Then the response returns the correct data
        self.assertStatus(response, 200)
        self.assertIn("cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87", response.data.decode())

        # We've removed the ru ref in the 'classifiers' key in the response as it's almost certainly not used anywhere.
        # This assertion will be removed if this is true, and we do another PR to remove the classifiers key.
        self.assertNotIn("test_ru_ref", response.data.decode())

    def test_get_instrument_by_search_string_type(self):
        # Given an instrument which is in the db
        instrument_id = self.add_instrument_without_exercise()

        # When the collection instrument end point is called with a search string
        response = self.client.get(
            '/collection-instrument-api/1.0.2/collectioninstrument?searchString={"TYPE":%20"EQ"}',
            headers=self.get_auth_headers(),
        )

        # Then the response returns the correct data
        self.assertStatus(response, 200)
        self.assertIn("cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87", response.data.decode())
        self.assertIn(str(instrument_id), response.data.decode())

    def test_get_instrument_by_search_classifier(self):
        # Given an instrument which is in the db
        # When the collection instrument end point is called with a search classifier
        response = self.client.get(
            '/collection-instrument-api/1.0.2/collectioninstrument?searchString={"FORM_TYPE":%20"001"}',
            headers=self.get_auth_headers(),
        )

        # Then the response returns the correct data
        self.assertStatus(response, 200)
        self.assertIn("test_file", response.data.decode())
        self.assertIn("001", response.data.decode())
        self.assertIn("cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87", response.data.decode())

    def test_get_instrument_by_search_multiple_classifiers(self):
        # Given an instrument which is in the db
        # When the collection instrument end point is called with a multiple search classifiers
        response = self.client.get(
            "/collection-instrument-api/1.0.2/collectioninstrument?"
            'searchString={"FORM_TYPE":%20"001","GEOGRAPHY":%20"EN"}',
            headers=self.get_auth_headers(),
        )

        # Then the response returns the correct data
        self.assertStatus(response, 200)
        self.assertIn("test_file", response.data.decode())
        self.assertIn('"geography": "EN"', response.data.decode())
        self.assertIn('"form_type": "001"', response.data.decode())
        self.assertIn("cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87", response.data.decode())

    def test_get_instrument_by_search_limit_1(self):
        # Given a 2nd instrument is added
        self.add_instrument_data()
        # When the collection instrument end point is called with limit set to 1
        response = self.client.get(
            "/collection-instrument-api/1.0.2/collectioninstrument?limit=1", headers=self.get_auth_headers()
        )

        # Then 1 response is returned
        self.assertStatus(response, 200)
        self.assertIn("test_file", response.data.decode())
        self.assertEqual(response.data.decode().count("cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"), 1)

    def test_get_instrument_by_search_limit_2(self):
        # Given a 2nd instrument is added
        self.add_instrument_data()
        # When the collection instrument end point is called with limit set to 2
        response = self.client.get(
            "/collection-instrument-api/1.0.2/collectioninstrument?limit=2", headers=self.get_auth_headers()
        )

        # Then 2 responses are returned
        self.assertStatus(response, 200)
        self.assertEqual(response.data.decode().count("cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"), 2)

    def test_count_instrument_by_search_string_ru(self):
        # Given an instrument which is in the db
        # When the collection instrument end point is called with a search string
        response = self.client.get(
            '/collection-instrument-api/1.0.2/collectioninstrument/count?searchString={"RU_REF":%20"test_ru_ref"}',
            headers=self.get_auth_headers(),
        )

        # Then the response returns the correct data
        self.assertStatus(response, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data, 1)

    def test_single_count_instrument(self):
        # Given an instrument which is in the db
        # When the collection instrument end point is called with a search string
        response = self.client.get(
            "/collection-instrument-api/1.0.2/collectioninstrument/count", headers=self.get_auth_headers()
        )

        # Then the response returns the correct data
        self.assertStatus(response, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data, 1)

    def test_multiple_count_instrument(self):
        # Given a second instrument in the db
        self.add_instrument_data()
        # When the collection instrument end point is called with a search string
        response = self.client.get(
            "/collection-instrument-api/1.0.2/collectioninstrument/count", headers=self.get_auth_headers()
        )

        # Then the response returns the correct data
        self.assertStatus(response, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data, 2)

    def test_count_instrument_by_search_classifier(self):
        # Given an instrument which is in the db
        # When the collection instrument end point is called with a search classifier
        response = self.client.get(
            '/collection-instrument-api/1.0.2/collectioninstrument/count?searchString={"FORM_TYPE":%20"001"}',
            headers=self.get_auth_headers(),
        )

        # Then the response returns the correct data
        self.assertStatus(response, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data, 1)

    def test_count_instrument_by_search_multiple_classifiers(self):
        # Given an instrument which is in the db
        # When the collection instrument end point is called with a multiple search classifiers
        response = self.client.get(
            "/collection-instrument-api/1.0.2/collectioninstrument/count?"
            'searchString={"FORM_TYPE":%20"001","GEOGRAPHY":%20"EN"}',
            headers=self.get_auth_headers(),
        )

        # Then the response returns the correct data
        self.assertStatus(response, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data, 1)

    def test_count_instrument_by_search_multiple_bad_classifiers(self):
        # Given an instrument which is in the db
        # When the collection instrument end point is called with a multiple search classifiers
        response = self.client.get(
            "/collection-instrument-api/1.0.2/collectioninstrument/count?"
            'searchString={"FORM_TYPE":%20"666","GEOGRAPHY":%20"GB"}',
            headers=self.get_auth_headers(),
        )

        # Then the response returns the correct data
        self.assertStatus(response, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data, 0)

    def test_get_instrument_by_id(self):
        # Given an instrument which is in the db
        # When the collection instrument end point is called with an id
        response = self.client.get(
            f"/collection-instrument-api/1.0.2/collectioninstrument/id/{self.instrument_id}",
            headers=self.get_auth_headers(),
        )

        # Then the response returns the correct data
        self.assertStatus(response, 200)
        self.assertIn("test_ru_ref", response.data.decode())
        self.assertIn("cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87", response.data.decode())

        # Given an instrument which is in the db
        # When the collection instrument end point is called with an id
        response = self.client.get(
            f"/collection-instrument-api/1.0.2/{self.instrument_id}",
            headers=self.get_auth_headers(),
        )

        # Then the response returns the correct data
        self.assertStatus(response, 200)
        self.assertIn("test_ru_ref", response.data.decode())
        self.assertIn("cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87", response.data.decode())

    def test_get_instrument_by_id_no_instrument(self):
        # Given an instrument which doesn't exist
        missing_instrument_id = "ffb8a5e8-03ef-45f0-a85a-3276e98f66b8"

        # When the collection instrument end point is called with an id
        response = self.client.get(
            f"/collection-instrument-api/1.0.2/collectioninstrument/id/{missing_instrument_id}",
            headers=self.get_auth_headers(),
        )

        # Then the response returns no data
        self.assertStatus(response, 404)
        self.assertEqual(response.data.decode(), COLLECTION_INSTRUMENT_NOT_FOUND)

        # When the collection instrument end point is called with an id
        response = self.client.get(
            f"/collection-instrument-api/1.0.2/{missing_instrument_id}",
            headers=self.get_auth_headers(),
        )

        # Then the response returns no data
        self.assertStatus(response, 404)
        self.assertEqual(response.data.decode(), COLLECTION_INSTRUMENT_NOT_FOUND)

    def test_download_exercise_csv_missing(self):
        # Given a incorrect exercise id
        # When a call is made to the download_csv end point
        response = self.client.get(
            "/collection-instrument-api/1.0.2/download_csv/d10711c3-0ac8-41d3-ae0e-567e5ea1ef87",
            headers=self.get_auth_headers(),
        )

        # Then a collection exercise is not found
        self.assertStatus(response, 404)
        self.assertEqual(response.data.decode(), NO_INSTRUMENT_FOR_EXERCISE)

    def test_get_instrument_download_missing_instrument(self):
        # Given an instrument which doesn't exist in the db
        instrument = "655488ea-ccaa-4d02-8f73-3d20bceed706"

        # When the collection instrument end point is called with an id
        response = self.client.get(
            f"/collection-instrument-api/1.0.2/download/{instrument}",
            headers=self.get_auth_headers(),
        )

        # Then the response returns a 404
        self.assertStatus(response, 404)

    def test_ras_error_in_session(self):
        # Given an upload file and a patched survey_id response which returns a RasError
        data = {"file": (BytesIO(b"test data"), "test.xls")}
        mock_survey_service = RasError("The service raised an error")

        with patch("application.controllers.collection_instrument.service_request", side_effect=mock_survey_service):
            # When a post is made to the upload end point
            response = self.client.post(
                "/collection-instrument-api/1.0.2/upload/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"
                '?classifiers={"form_type": "001"}',
                headers=self.get_auth_headers(),
                data=data,
                content_type="multipart/form-data",
            )

        # Then a error is reported
        self.assertIn("The service raised an error", response.data.decode())

    @staticmethod
    def get_auth_headers():
        auth = "{}:{}".format(
            current_app.config.get("SECURITY_USER_NAME"), current_app.config.get("SECURITY_USER_PASSWORD")
        ).encode("utf-8")
        return {"Authorization": "Basic %s" % base64.b64encode(bytes(auth)).decode("ascii")}

    def test_instrument_by_search_string_ru_missing_auth_details(self):
        # Given an instrument which is in the db
        # When the collection instrument end point is called without auth details
        response = self.client.get(
            '/collection-instrument-api/1.0.2/collectioninstrument?searchString={"RU_REF":%20"test_ru_ref"}'
        )

        # Then a 401 unauthorised is return
        self.assertStatus(response, 401)

    def test_instrument_by_search_string_ru_incorrect_auth_details(self):
        # Given a file and incorrect auth details
        auth = "{}:{}".format("incorrect_user_name", "incorrect_password").encode("utf-8")
        header = {"Authorization": "Basic %s" % base64.b64encode(bytes(auth)).decode("ascii")}

        # When the collection instrument end point is called with incorrect auth details
        response = self.client.get(
            '/collection-instrument-api/1.0.2/collectioninstrument?searchString={"RU_REF":%20"test_ru_ref"}',
            headers=header,
        )

        # Then a 401 unauthorised is return
        self.assertStatus(response, 401)

    @requests_mock.mock()
    def test_link_collection_instrument(self, mock_request):
        mock_request.post(url_collection_instrument_link_url, status_code=200)

        # Given an instrument which is in the db is not linked to a collection exercise
        instrument_id = self.add_instrument_without_exercise()
        exercise_id = "c3c0403a-6e9c-46f6-af5e-5f67fefb2a9d"
        # When the instrument is linked to an exercise
        response = self.client.post(
            f"/collection-instrument-api/1.0.2/link-exercise/{instrument_id}/{exercise_id}",
            headers=self.get_auth_headers(),
        )

        # Then that instrument is successfully linked to the given collection exercise
        self.assertStatus(response, 200)
        linked_exercises = collection_exercises_linked_to_collection_instrument(instrument_id)
        linked_exercise_ids = [str(collection_exercise.exercise_id) for collection_exercise in linked_exercises]
        self.assertIn(exercise_id, linked_exercise_ids)

    @requests_mock.mock()
    def test_link_collection_instrument_rest_exception(self, mock_request):
        mock_request.post(url_collection_instrument_link_url, status_code=500)
        # Given an instrument which is in the db is not linked to a collection exercise
        instrument_id = self.add_instrument_without_exercise()
        exercise_id = "c3c0403a-6e9c-46f6-af5e-5f67fefb2a9d"

        # When the instrument is linked to an exercise
        with self.assertRaises(Exception):
            response = self.client.post(
                f"/collection-instrument-api/1.0.2/link-exercise/{instrument_id}/{exercise_id}",
                headers=self.get_auth_headers(),
            )

            response_data = json.loads(response.data)

            self.assertStatus(response, 500)
            self.assertEqual(response_data["errors"][0], "Failed to publish upload message")

    @requests_mock.mock()
    def test_unlink_eq_collection_instrument(self, mock_request):
        # Given an eq instrument which is in the db is linked to a collection exercise
        mock_request.post(url_collection_instrument_link_url, status_code=200)
        eq_instrument_id = self.add_instrument_data(ci_type="EQ")

        # When the instrument is unlinked to an exercise
        response = self.client.put(
            f"/collection-instrument-api/1.0.2/unlink-exercise/{eq_instrument_id}/{linked_exercise_id}",
            headers=self.get_auth_headers(),
        )

        # Then that instrument and collection exercise are successfully unlinked
        self.assertStatus(response, 200)
        linked_exercises = collection_exercises_linked_to_collection_instrument(eq_instrument_id)
        linked_exercise_ids = [str(collection_exercise.exercise_id) for collection_exercise in linked_exercises]
        self.assertNotIn(linked_exercise_id, linked_exercise_ids)

    @requests_mock.mock()
    def test_unlink_eq_collection_instrument_rest_exception(self, mock_request):
        mock_request.post(url_collection_instrument_link_url, status_code=500)
        # Given an eq instrument which is in the db is linked to a collection exercise
        eq_instrument_id = self.add_instrument_data(ci_type="EQ")

        # When the instrument is unlinked to an exercise but failed to publish messsage
        response = self.client.put(
            f"/collection-instrument-api/1.0.2/unlink-exercise/{eq_instrument_id}/{linked_exercise_id}",
            headers=self.get_auth_headers(),
        )

        self.assertStatus(response, 500)

    @requests_mock.mock()
    def test_unlink_eq_collection_instrument_does_not_unlink_all_ci_to_given_ce(self, mock_request):
        mock_request.post(url_collection_instrument_link_url, status_code=200)
        # Given there are multiple cis linked to the same ce
        eq_instrument_id = self.add_instrument_data(ci_type="EQ")
        instrument_without_exercise = self.add_instrument_without_exercise()

        self.client.post(
            f"/collection-instrument-api/1.0.2/link-exercise/{instrument_without_exercise}/{linked_exercise_id}",
            headers=self.get_auth_headers(),
        )

        # When the instrument is unlinked to an exercise
        response = self.client.put(
            f"/collection-instrument-api/1.0.2/unlink-exercise/{eq_instrument_id}/{linked_exercise_id}",
            headers=self.get_auth_headers(),
        )

        # Then only that ci and ce are unlinked the other link remains
        self.assertStatus(response, 200)

        linked_exercises = collection_exercises_linked_to_collection_instrument(eq_instrument_id)
        linked_exercise_ids = [str(collection_exercise.exercise_id) for collection_exercise in linked_exercises]
        self.assertNotIn(linked_exercise_id, linked_exercise_ids)

        linked_exercises = collection_exercises_linked_to_collection_instrument(instrument_without_exercise)
        linked_exercise_ids = [str(collection_exercise.exercise_id) for collection_exercise in linked_exercises]
        self.assertIn(linked_exercise_id, linked_exercise_ids)

    def test_unlink_collection_instrument_not_found_ci(self):
        # given we have an unknown collection instrument id
        unknown_ci = "c3c0403a-6e9c-46f6-af5e-5f67fefb2a9d"

        # When unlink call made with
        response = self.client.put(
            f"/collection-instrument-api/1.0.2/unlink-exercise/{unknown_ci}/{linked_exercise_id}",
            headers=self.get_auth_headers(),
        )
        # Then 404 not found error returned
        response_data = json.loads(response.data)

        self.assertStatus(response, 404)
        self.assertEqual(response_data["errors"][0], "Unable to find instrument or exercise")

    @requests_mock.mock()
    def test_update_eq_instruments(self, mock_request):
        # Given an instrument which is in the db is not linked to a collection exercise
        mock_request.post(url_collection_instrument_link_url, status_code=200)
        instrument_id = self.add_instrument_without_exercise()
        exercise_id = "c3c0403a-6e9c-46f6-af5e-5f67fefb2a9d"
        # When the instrument is linked to an exercise
        response = self.client.post(
            f"/collection-instrument-api/1.0.2/update-eq-instruments/{exercise_id}?"
            f"instruments={str(instrument_id)}",
            headers=self.get_auth_headers(),
        )

        # Then that instrument is successfully linked to the given collection exercise
        self.assertStatus(response, 200)
        linked_collection_instruments, collection_exercise_id = collection_exercises_and_collection_instrument(
            exercise_id
        )
        linked_collection_instrument = [str(ci.instrument_id) for ci in linked_collection_instruments]
        self.assertIn(str(instrument_id), linked_collection_instrument)
        self.assertIn(exercise_id, str(collection_exercise_id))

    @requests_mock.mock()
    def test_publish_collection_instrument_to_collection_exercise_rest_failure_for_ci_http_error(self, mock_request):
        mock_request.post(url_collection_instrument_link_url, status_code=400)
        instrument_id = self.add_instrument_without_exercise()
        exercise_id = "c3c0403a-6e9c-46f6-af5e-5f67fefb2a9d"

        response = self.client.post(
            f"/collection-instrument-api/1.0.2/update-eq-instruments/{exercise_id}?"
            f"instruments={str(instrument_id)}",
            headers=self.get_auth_headers(),
        )

        response_data = json.loads(response.data)
        print("Test response: " + str(response_data))
        self.assertStatus(response, 400)
        self.assertEqual(response_data["errors"][0], "collection exercise responded with an http error")

    @requests_mock.mock()
    def test_remove_update_collection_exercise_instruments(self, mock_request):
        # Given an instrument which is in the db is linked to a collection exercise
        mock_request.post(url_collection_instrument_link_url, status_code=200)
        instrument_id = self.add_instrument_without_exercise()
        exercise_id = "c3c0403a-6e9c-46f6-af5e-5f67fefb2a9d"
        # And the instrument is linked to an exercise
        self.client.post(
            f"/collection-instrument-api/1.0.2/update-eq-instruments/{exercise_id}?"
            f"instruments={str(instrument_id)}",
            headers=self.get_auth_headers(),
        )

        collection_exercises_and_collection_instrument(exercise_id)

        # When the instrument is unlinked to an exercise
        response = self.client.post(
            f"/collection-instrument-api/1.0.2/update-eq-instruments/{exercise_id}",
            headers=self.get_auth_headers(),
        )

        # Then that instrument and collection exercise are successfully unlinked
        self.assertStatus(response, 200)
        linked_collection_instruments, collection_exercise_id = collection_exercises_and_collection_instrument(
            exercise_id
        )
        linked_collection_instrument = [str(ci.instrument_id) for ci in linked_collection_instruments]
        self.assertIn(exercise_id, str(collection_exercise_id))
        self.assertNotIn(str(instrument_id), linked_collection_instrument)

    @requests_mock.mock()
    def test_patch_collection_instrument_empty_file(self, mock_request):
        mock_request.get(survey_url, status_code=200, json=survey_response_json)

        # When patch call made
        data = {"file": (BytesIO(), "test.xls")}

        response = self.client.patch(
            f"/collection-instrument-api/1.0.2/{self.instrument_id}",
            data=data,
            content_type="multipart/form-data",
            headers=self.get_auth_headers(),
        )

        # Then 400 not found error returned
        response_data = json.loads(response.data)

        self.assertEqual(response_data["errors"][0], "File is empty")
        self.assertStatus(response, 400)

    def test_patch_collection_instrument_missing_filename(self):
        # given we have a collection instrument id
        instrument_id = "c3c0403a-6e9c-46f6-af5e-5f67fefb2a9d"

        # When patch call made
        data = {"file": (BytesIO(b"text"), "")}

        response = self.client.patch(
            f"/collection-instrument-api/1.0.2/{instrument_id}",
            data=data,
            content_type="multipart/form-data",
            headers=self.get_auth_headers(),
        )

        # Then 400 not found error returned
        response_data = json.loads(response.data)

        self.assertEqual(response_data["errors"][0], "Missing filename")
        self.assertStatus(response, 400)

    @requests_mock.mock()
    @mock.patch("application.controllers.collection_instrument.GoogleCloudSEFTCIBucket")
    def test_patch_collection_instrument_gcs(self, mock_request, mock_bucket):
        mock_request.get(survey_url, status_code=200, json=survey_response_json)

        mock_bucket.return_value.upload_file_to_bucket.return_value = "file_path.xlsx"
        # When patch call made
        data = {"file": (BytesIO(b"test data"), "test.xls")}

        response = self.client.patch(
            f"/collection-instrument-api/1.0.2/{self.instrument_id}",
            data=data,
            content_type="multipart/form-data",
            headers=self.get_auth_headers(),
        )

        self.assertStatus(response, 200)
        self.assertEqual(response.data.decode(), "The patch of the instrument was successful")

    @staticmethod
    @with_db_session
    def add_instrument_without_exercise(session=None):
        instrument = InstrumentModel(ci_type="EQ", classifiers={"form_type": "001", "geography": "EN"})
        survey = SurveyModel(survey_id="cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87")
        instrument.survey = survey
        business = BusinessModel(ru_ref="test_ru_ref")
        instrument.businesses.append(business)
        session.add(instrument)
        return instrument.instrument_id

    @staticmethod
    @with_db_session
    def add_collection_exercise(session=None):
        exercise_id = "fb2a9d3a-6e9c-46f6-af5e-5f67fec3c040"
        collection_exercise = ExerciseModel(exercise_id=exercise_id)
        collection_instruments = InstrumentModel(ci_type="EQ", classifiers={"form_type": "001", "geography": "EN"})
        collection_exercise.instruments.append(collection_instruments)
        session.add(collection_exercise)
        return collection_exercise

    @staticmethod
    @with_db_session
    def add_instrument_data(session=None, ci_type="SEFT"):
        instrument = InstrumentModel(classifiers={"form_type": "001", "geography": "EN"}, ci_type=ci_type)
        if ci_type == "SEFT":
            seft_file = SEFTModel(instrument_id=instrument.instrument_id, file_name="test_file", length="999")
            instrument.seft_file = seft_file
            business = BusinessModel(ru_ref="test_ru_ref")
            instrument.businesses.append(business)
        exercise = ExerciseModel(exercise_id=linked_exercise_id)
        instrument.exercises.append(exercise)
        survey = SurveyModel(survey_id="cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87")
        instrument.survey = survey
        session.add(instrument)
        return instrument.instrument_id
