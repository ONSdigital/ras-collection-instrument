##############################################################################
#                                                                            #
#   Collection Instruments Upload                                            #
#   Date:    11 May 2017                                                     #
#   Author:  Gareth Bult                                                     #
#   License: MIT                                                             #
#   Copyright (c) 2017 Crown Copyright (Office for National Statistics)      #
#                                                                            #
##############################################################################
from . import BaseTestCase
from werkzeug.datastructures import FileStorage
from six import BytesIO
from ..controllers_local.collectioninstrument import CollectionInstrument
from uuid import uuid4

DEFAULT_SURVEY = "3decb89c-c5f5-41b8-9e74-5033395d247e"


class TestCiuploadController(BaseTestCase):
    """ CiuploadController integration test stubs """

    def setUp(self):
        """
        The collection_instrument variable represents the external class we're about to exercise ...
        """
        super()
        self.collection_instrument = CollectionInstrument()

    def test_01_define_batch(self):
        """
        Make sure we can define a batch
        """
        code, msg = self.collection_instrument.define_batch(str(uuid4()), 100)
        self.assertTrue(code == 200, msg)
        try:
            code, msg = self.collection_instrument.define_batch(0, 100)
            self.assertTrue(code == 200, msg)
        except:
            pass

    def test_03_upload(self):
        """
        Try a valid upload, and also an upload to an undefined batch
        """
        with open('scripts/upload.txt', 'rb') as io:
            fileobject = FileStorage(stream=io, filename='dummy.txt', name='myname')
            code, msg = self.collection_instrument.upload(str(uuid4()), fileobject, 'dummy.txt')
            self.assertTrue(code == 200, msg)

        with open('scripts/upload.txt', 'rb') as io:
            fileobject = FileStorage(stream=io, filename='dummy.txt', name='myname')
            code, msg = self.collection_instrument.upload(0, fileobject, 'dummy.txt')
            self.assertTrue(code == 400, msg)

    def test_04_csv(self):
        """
        Upload a file, then make sure we are able to download the result in CSV format
        """
        batch = str(uuid4())
        with open('scripts/upload.txt', 'rb') as io:
            fileobject = FileStorage(stream=io, filename='dummy.txt', name='myname')
            code, msg = self.collection_instrument.upload(batch, fileobject, 'dummy.txt')
            self.assertTrue(code == 200, msg)

        code, msgs = self.collection_instrument.csv(batch)
        msg = msgs.split('\n')[1][:21]
        wanted = '"1","dummy.txt","24",'
        self.assertTrue(msg == wanted, "CSV download")
        code, msg = self.collection_instrument.csv(str(uuid4()))
        self.assertTrue(code == 204, "CSV download")
        try:
            code, msg = self.collection_instrument.csv(0)
        except Exception:
            pass
        self.assertTrue(code == 400, "CSV download")
        try:
            code, msg = self.collection_instrument.csv('0')
        except Exception:
            pass
        self.assertTrue(code == 500, "CSV download")



    def test_05_status(self):
        """
        Make sure a /status works and that it see's an attempt to /status an undefined batch 
        """
        batch = str(uuid4())
        code, msg = self.collection_instrument.define_batch(batch, 100)
        self.assertTrue(code == 200, msg)
        code, msg = self.collection_instrument.status(batch)
        self.assertTrue(code == 200, msg)
        code, msg = self.collection_instrument.status(str(uuid4()))
        self.assertTrue(code == 204, msg)
        try:
            code, msg = self.collection_instrument.define_batch(str(uuid4()), 100)
        except Exception:
            pass
        self.assertTrue(code == 200, msg)
        try:
            code, msg = self.collection_instrument.status(0)
        except Exception:
            pass
        self.assertTrue(code == 400, msg)


    def test_06_activate(self):
        """        
        Check an activate works, make sure we spot an invalid state, and an undefined batch
        """
        batch = str(uuid4())
        code, msg = self.collection_instrument.define_batch(batch, 100)
        self.assertTrue(code == 200, msg)
        code, msg = self.collection_instrument.activate(batch)
        self.assertTrue(code == 200, msg)
        self.collection_instrument._exercise_status_set(batch, 'active')
        code, msg = self.collection_instrument.activate(batch)
        self.assertTrue(code == 500, msg)
        code, msg = self.collection_instrument.activate(str(uuid4()))
        self.assertTrue(code == 204, msg)
        try:
            code, msg = self.collection_instrument.activate(0)
        except Exception:
            pass
        self.assertTrue(code == 400, msg)


    def test_07_upload(self):
        """
        This is the really fun bit (!) we're need to contact the endpoint directly and make sure we can upload
        a file to at. We need to pick up on uploads with no file attached, and uploads to undefined batches.
        """
        batch = str(uuid4())
        data = dict(upfile=(BytesIO(b'some file data'), 'file.txt'))
        response = self.client.open(
            '/collection-instrument-api/1.0.2/upload/{ref}/{file}'.format(ref=batch,file='fred.txt'),
            method='POST',
            data=data,
            content_type='multipart/form-data')
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))
        response = self.client.open(
            '/collection-instrument-api/1.0.2/upload/{ref}/{file}'.format(ref=batch,file='fred.txt'),
            method='POST',
            data='',
            content_type='multipart/form-data')
        self.assert500(response, "Response body is : " + response.data.decode('utf-8'))
        data = dict(upfile=(BytesIO(b'some file data'), 'file.txt'))
        response = self.client.open(
            '/collection-instrument-api/1.0.2/upload/{ref}/{file}'.format(ref=str(uuid4()), file='fred.txt'),
            method='POST',
            data=data,
            content_type='multipart/form-data')
        self.assertTrue(response.status_code == 200, "Response body is : " + response.data.decode('utf-8'))
        data = dict(upfile=(BytesIO(b'some file data'), 'file.txt'))
        response = self.client.open(
            '/collection-instrument-api/1.0.2/upload/{ref}/{file}'.format(ref="1", file='fred.txt'),
            method='POST',
            data=data,
            content_type='multipart/form-data')
        self.assertTrue(response.status_code == 500, "Response body is : " + response.data.decode('utf-8'))

    def test_08_download(self):
        """
        Upload a document, encrypt, store, then recover, decrypt and make sure it's what
        we started with ...
        """
        batch = str(uuid4())
        with open('scripts/upload.txt', 'rb') as io:
            fileobject = FileStorage(stream=io, filename='dummy.txt', name='myname')
            code, msg = self.collection_instrument.upload(batch, fileobject, 'my_RU_code')
            self.assertTrue(code == 200, msg)

        code, msg = self.collection_instrument.instruments('{"ru_ref": "my_RU_code"}')
        self.assertTrue(code == 200, msg)

        code, msg = self.collection_instrument.download("my_RU_code")
        with open('scripts/upload.txt', 'rb') as io:
            orig = io.read()
        self.assertEqual(msg, orig, 'Comparing processed with original')
        code, msg = self.collection_instrument.download('does_not_exist')
        self.assertTrue(code == 404, msg)
        code, msg = self.collection_instrument.download(0)
        self.assertTrue(code == 400, msg)

    def test_09_misc(self):
        """
        Test misc (not required?) routines
        """
        batch = str(uuid4())
        with open('scripts/upload.txt', 'rb') as io:
            fileobject = FileStorage(stream=io, filename='dummy.txt', name='myname')
            code, msg = self.collection_instrument.upload(batch, fileobject, 'my_RU_code')
            self.assertTrue(code == 200, msg)

        code, msg = self.collection_instrument.instruments('{"ru_ref": "my_RU_code"}')
        self.assertTrue(code == 200, msg)
        instrument = msg[0]
        instrument_id = str(instrument['id'])

        code, msg = self.collection_instrument.instrument(str(uuid4()))
        self.assertTrue(code == 404, msg)

        code, msg = self.collection_instrument.instrument(instrument_id)
        self.assertTrue(code == 200, 'Instrument fetch by id')

        try:
            code, msg = self.collection_instrument.instrument('abc')
        except Exception:
            pass
        self.assertTrue(code == 500, msg)

        try:
            code, msg = self.collection_instrument.instrument(0)
        except Exception:
            pass
        self.assertTrue(code == 400, 'Failed to lookup instrument with integer id')

        try:
            code, msg = self.collection_instrument.instrument()
        except Exception:
            pass
        self.assertTrue(code == 500, msg)

        try:
            code, msg = self.collection_instrument.instruments('{"NO CODE": "NO VALUE"}')
        except:
            pass
        self.assertTrue(code == 500, 'No such classifier')

        try:
            code, msg = self.collection_instrument.instruments(123)
        except TypeError:
            pass
        except Exception:
            self.assertTrue(code == 500, 'Instrument with null')

    def test_10_clear(self):
        """
        Make sure we can clear a batch, and that we recognise a 'no such batch'
        """
        batch = str(uuid4())
        with open('scripts/upload.txt', 'rb') as io:
            fileobject = FileStorage(stream=io, filename='dummy.txt', name='myname')
            code, msg = self.collection_instrument.upload(batch, fileobject, 'my_RU_code')
            self.assertTrue(code == 200, msg)

        code, msg = self.collection_instrument.clear(batch)
        self.assertTrue(code == 200, msg)
        code, msg = self.collection_instrument.clear(str(uuid4()))
        self.assertTrue(code == 204, msg)
        with open('scripts/upload.txt', 'rb') as io:
            fileobject = FileStorage(stream=io, filename='dummy.txt', name='myname')
            code, msg = self.collection_instrument.upload(batch, fileobject, 'my_RU_code')
            self.assertTrue(code == 200, msg)
        code, msg = self.collection_instrument.clear(batch)
        self.assertTrue(code == 200, msg)
        code, msg = self.collection_instrument.clear(0)
        self.assertTrue(code == 400, msg)

    def test_11_instruments(self):
        """
        Try out some of the query by classifier options
        """
        batch = str(uuid4())
        with open('scripts/upload.txt', 'rb') as io:
            fileobject = FileStorage(stream=io, filename='dummy.txt', name='myname')
            code, msg = self.collection_instrument.upload(batch, fileobject, 'file1')
            self.assertTrue(code == 200, msg)
        with open('scripts/upload.txt', 'rb') as io:
            fileobject = FileStorage(stream=io, filename='dummy.txt', name='myname')
            code, msg = self.collection_instrument.upload(batch, fileobject, 'file2')
            self.assertTrue(code == 200, msg)
        with open('scripts/upload.txt', 'rb') as io:
            fileobject = FileStorage(stream=io, filename='dummy.txt', name='myname')
            code, msg = self.collection_instrument.upload(batch, fileobject, 'file3')
            self.assertTrue(code == 200, msg)

        code, msg = self.collection_instrument.instruments('')
        self.assertTrue(code == 200, msg)

        code, msg = self.collection_instrument.instruments('{"ru_ref": "file3"}')
        self.assertTrue(code == 200, msg)
        code, msg = self.collection_instrument.instruments('{"exercise": "'+batch+'"}')
        self.assertTrue(code == 200, msg)
        code, msg = self.collection_instrument.instruments('{"survey": "'+DEFAULT_SURVEY+'"}')
        self.assertTrue(code == 200, msg)
        code, msg = self.collection_instrument.instruments('{"SIZE": "1234"}')
        self.assertTrue(code == 200, msg)



if __name__ == '__main__':
    import unittest
    unittest.main()
