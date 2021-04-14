import base64
from uuid import UUID

from application.exceptions import RasError


def is_valid_file_extension(file_name, extensions):
    """
    Check the file format is valid

    :param file_name: The file name to be checked
    :param extensions: The list of extensions that are valid
    :return: boolean
    """
    return file_name.endswith(tuple(ext.strip() for ext in extensions.split(",")))


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

    :param file: The file to convert
    :return: String
    """
    return base64.b64encode(file).decode()


def to_str(bytes_or_str):
    """
    Convert supplied value to a string.  If supplied value of type str, this will return the value untouched

    :param bytes_or_str: bytes_or_str
    :return: value
    """
    if isinstance(bytes_or_str, bytes):
        return bytes_or_str.decode()
    return bytes_or_str


def validate_uuid(*values):
    """
    validate value is a uuid

    :param values: array of values to check
    :return: boolean
    """
    for value in values:
        try:
            UUID(value)
        except ValueError:
            raise RasError(f'Value is not a valid UUID ({value})', 400)
        return True
