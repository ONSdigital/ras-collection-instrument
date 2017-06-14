# coding: utf-8

from __future__ import absolute_import

from swagger_server.models.collectioninstrument import Collectioninstrument
from . import BaseTestCase
from six import BytesIO
from flask import json


class TestRespondentController(BaseTestCase):
    """ RespondentController integration test stubs """

    def test_collectioninstrument_get(self):
        """
        Test case for collectioninstrument_get

        searches collection instruments
        """
        query_string = [('searchString', 'searchString_example'),
                        ('skip', 1),
                        ('limit', 50)]
        response = self.client.open('/collection-instrument-api/1.0.3/collectioninstrument',
                                    method='GET',
                                    query_string=query_string)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_get_collection_instrument_by_id(self):
        """
        Test case for get_collection_instrument_by_id

        Get a collection instrument by ID
        """
        response = self.client.open('/collection-instrument-api/1.0.3/collectioninstrument/id/{id}'.format(id='id_example'),
                                    method='GET')
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
