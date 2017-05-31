# coding: utf-8

from __future__ import absolute_import

from . import BaseTestCase
from six import BytesIO
from flask import json


class TestCiuploadController(BaseTestCase):
    """ CiuploadController integration test stubs """

    def test_activate_id_put(self):
        """
        Test case for activate_id_put

        Activate batch
        """
        response = self.client.open('/collection-instrument-api/1.0.2/activate/{id}'.format(id='id_example'),
                                    method='PUT')
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_clear_batch_id_delete(self):
        """
        Test case for clear_batch_id_delete

        Clear a batch
        """
        response = self.client.open('/collection-instrument-api/1.0.2/clear_batch/{id}'.format(id='id_example'),
                                    method='DELETE')
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_define_batch_id_count_post(self):
        """
        Test case for define_batch_id_count_post

        Specify the size of a batch
        """
        response = self.client.open('/collection-instrument-api/1.0.2/define_batch/{id}/{count}'.format(id='id_example', count=56),
                                    method='POST')
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_download_csv_id_get(self):
        """
        Test case for download_csv_id_get

        Download CSV file
        """
        response = self.client.open('/collection-instrument-api/1.0.2/download_csv/{id}'.format(id='id_example'),
                                    method='GET')
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_download_id_get(self):
        """
        Test case for download_id_get

        Download a file based on the id (RU_REF)
        """
        response = self.client.open('/collection-instrument-api/1.0.2/download/{id}'.format(id='id_example'),
                                    method='GET',
                                    content_type='multipart/form-data')
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_status_id_get(self):
        """
        Test case for status_id_get

        Get upload status
        """
        response = self.client.open('/collection-instrument-api/1.0.2/status/{id}'.format(id='id_example'),
                                    method='GET')
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_upload_id_file_post(self):
        """
        Test case for upload_id_file_post

        Upload collection instrument
        """
        data = dict(files=(BytesIO(b'some file data'), 'file.txt'))
        response = self.client.open('/collection-instrument-api/1.0.2/upload/{id}/{file}'.format(id='id_example', file='file_example'),
                                    method='POST',
                                    data=data,
                                    content_type='multipart/form-data')
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
