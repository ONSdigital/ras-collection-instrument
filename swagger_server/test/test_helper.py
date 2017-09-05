import unittest

from swagger_server.controllers.helper import convert_string_to_bytes_base64, \
    convert_file_object_to_string_base64, to_str, to_bytes, is_valid_file_extension, is_valid_file_name_length

from werkzeug.datastructures import FileStorage

TEST_FILE_LOCATION = 'swagger_server/test/test.xlsx'


class TestHelper(unittest.TestCase):
    """ Helper unit tests"""

    def test_file_object_to_string_base64(self):

        # Given a file
        with open(TEST_FILE_LOCATION, 'rb') as io:
            file = FileStorage(stream=io, filename='test.xlsx')

            # When it is converted to a string
            f = file.read()
            file_as_string = convert_file_object_to_string_base64(f)

            # Then it is a string
            self.assertEquals(type(file_as_string), str)

    def test_string_to_file_object(self):

        # Given a file has been converted to a string
        with open(TEST_FILE_LOCATION, 'rb') as io:
            file = FileStorage(stream=io, filename='test.xlsx')
            f = file.read()
            file_as_string = convert_file_object_to_string_base64(f)

            # When it is converted to bytes
            string_as_bytes = convert_string_to_bytes_base64(file_as_string)

            # Then it is a byte stream
            self.assertEquals(type(string_as_bytes), bytes)

    def test_valid_file_format_true(self):

        # Given a valid file extension and a list of extensions
        file_name = 'test.xlsx'
        file_extension = 'xlsx'

        # When is valid file format is called
        result = is_valid_file_extension(file_name, file_extension)

        # Then it is True
        self.assertTrue(result)

    def test_valid_file_format_false(self):

        # Given an invalid file extension and a list of extensions
        file_name = 'test.txt'
        file_extension = 'xlsx'

        # When is valid file format is called
        result = is_valid_file_extension(file_name, file_extension)

        # Then it is False
        self.assertFalse(result)

    def test_is_valid_file_name_length_true(self):

        # Given an valid file name length
        file_name = 'test.txt'
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
        value = None

        # When to_str is called
        s = to_str(None)

        # Then None is returned
        self.assertEqual(s, None)
