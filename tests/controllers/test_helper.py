import unittest

from application.controllers.helper import convert_string_to_bytes_base64, validate_uuid, \
    convert_file_object_to_string_base64, to_str, to_bytes, is_valid_file_extension, is_valid_file_name_length
from werkzeug.datastructures import FileStorage
from ras_common_utils.ras_error.ras_error import RasError

TEST_FILE_LOCATION = 'tests/files/test.xlsx'


class TestHelper(unittest.TestCase):
    """ Helper unit tests"""

    def test_file_object_to_string_base64(self):

        # Given a file
        with open(TEST_FILE_LOCATION, 'rb') as io:
            file = FileStorage(stream=io, filename='tests.xlsx')

            # When it is converted to a string
            f = file.read()
            file_as_string = convert_file_object_to_string_base64(f)

            # Then it is a string
            self.assertEquals(type(file_as_string), str)

    def test_string_to_file_object(self):

        # Given a file has been converted to a string
        with open(TEST_FILE_LOCATION, 'rb') as io:
            file = FileStorage(stream=io, filename='tests.xlsx')
            f = file.read()
            file_as_string = convert_file_object_to_string_base64(f)

            # When it is converted to bytes
            string_as_bytes = convert_string_to_bytes_base64(file_as_string)

            # Then it is a byte stream
            self.assertEquals(type(string_as_bytes), bytes)

    def test_valid_file_format_true(self):

        # Given a valid file extension and a list of extensions
        file_name = 'tests.xlsx'
        file_extension = 'xlsx'

        # When is valid file format is called
        result = is_valid_file_extension(file_name, file_extension)

        # Then it is True
        self.assertTrue(result)

    def test_valid_file_format_false(self):

        # Given an invalid file extension and a list of extensions
        file_name = 'tests.txt'
        file_extension = 'xlsx'

        # When is valid file format is called
        result = is_valid_file_extension(file_name, file_extension)

        # Then it is False
        self.assertFalse(result)

    def test_is_valid_file_name_length_true(self):

        # Given an valid file name length
        file_name = 'tests.txt'
        length = 10

        # When is valid file format is called
        result = is_valid_file_name_length(file_name, length)

        # Then it is True
        self.assertTrue(result)

    def test_is_valid_file_name_length_false(self):

        # Given an invalid file name length
        file_name = 'abcdefghijklmnopqrstuvwxyz.txt'
        length = 10

        # When is valid file format is called
        result = is_valid_file_name_length(file_name, length)

        # Then it is False
        self.assertFalse(result)

    def test_to_bytes_with_string(self):

        # Given a string
        string = 'abc'

        # When to_bytes is called
        b = to_bytes(string)

        # Then a byte stream is returned
        self.assertEqual(b, b'abc')

    def test_to_bytes_with_bytes(self):

        # Given a byte stream
        bytes_stream = b'def'

        # When to_bytes is called
        b = to_bytes(bytes_stream)

        # Then a byte stream is returned
        self.assertEqual(b, b'def')

    def test_to_bytes_with_none(self):
        # Given nothing is passed
        value = None

        # When to_bytes is called
        b = to_bytes(value)

        # Then None is returned
        self.assertEqual(b, None)

    def test_to_string_with_string(self):

        # Given a string is passed
        string = 'hij'

        # When to_str is called
        s = to_str(string)

        # Then a string is returned
        self.assertEqual(s, 'hij')

    def test_to_string_with_bytes(self):

        # Given a bytes stream is passed
        byte_stream = b'klm'

        # When to_str is called
        s = to_str(byte_stream)

        # Then a string is returned
        self.assertEqual(s, 'klm')

    def test_to_string_with_none(self):

        # Given nothing is passed
        # When to_str is called
        s = to_str(None)

        # Then None is returned
        self.assertEqual(s, None)

    def test_validate_uuid(self):

        # Given a valid uuid
        uuid = ['6710e50e-224b-4918-9706-c6b28f7481cd']

        # When a call is made to validate_uuid
        is_valid_uuid = validate_uuid(uuid)

        # Then True is returned
        self.assertTrue(is_valid_uuid)

    def test_validate_uuid_error(self):

        # Given a invalid uuid
        uuid = ['invalid_uuid']

        # When a call is made to validate_uuid
        # Then an RasError is raised
        with self.assertRaises(RasError):
            validate_uuid(uuid)