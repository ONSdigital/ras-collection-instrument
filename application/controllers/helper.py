import base64

from application.exceptions import RasError
from uuid import UUID


def is_valid_file_extension(file_name, extensions):
    """
    Check the file format is valid
    :param file_name: The file name to be checked
    :param extensions: The list of extensions that are valid
    :return: boolean
    """
    return file_name.endswith(tuple(extensions.split(",")))


def is_valid_file_name_length(file_name, length):
    """
    Check the file name length is valid
    :param file_name: The file name to be checked
    :param length: The length of file name which is valid
    :return: boolean
    """
    return len(file_name) <= int(length)


def convert_file_object_to_string_base64(file):
    """
    Convert a file object to a string
    :param file: The file to conver
    :return: String
    """
    return base64.b64encode(file).decode()


def convert_string_to_bytes_base64(string):
    """
    Convert a string to bytes
    :param string: The string to convert to bytes
    :return: byte stream
    """
    encoded_string = string.encode()
    stream = base64.b64decode(encoded_string)
    return stream


def to_bytes(bytes_or_str):
    """
    Convert to bytes
    :param bytes_or_str: bytes_or_str
    :return: value
    """
    if isinstance(bytes_or_str, str):
        value = bytes_or_str.encode()
    else:
        value = bytes_or_str
    return value


def to_str(bytes_or_str):
    """
    Convert to string
    :param bytes_or_str: bytes_or_str
    :return: value
    """
    if isinstance(bytes_or_str, bytes):
        value = bytes_or_str.decode()
    else:
        value = bytes_or_str
    return value


def validate_uuid(values):
    """
    validate value is a uuid
    :param values: array of values to check
    :return: boolean
    """
    for value in values:
        try:
            UUID(value)
        except ValueError:
            raise RasError('Value is not a valid UUID ({})'.format(value), 500)
        return True
