#!/usr/bin/env python
import xlsxwriter
import requests
import sys
import os


END_POINT = '{}/collection-instrument-api/1.0.2/upload/{}/{}'
FILE_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


def upload_test_collection_instruments(app_url, exercise_id, basic_auth_username, basic_auth_password):
    """
    This function takes the values in 'ru_ref_import.txt' creates a xls for each and then uploads them
    to the desired application.
    :param app_url: The url of the application, should not include end point
    :param exercise_id: The exercise id of the upload
    :param basic_auth_username: The basic auth username for the service
    :param basic_auth_password: The basic auth password for the service
    """

    with open('ru_ref_import.txt') as io:
        while True:
            line_data = io.readline()
            if not line_data:
                break
            ru_ref = line_data.split('"')[1]
            file_name = ru_ref + '.xlsx'
            create_xls_file(file_name, ru_ref)

            file = {'file': (file_name, open(file_name, 'rb'), FILE_TYPE)}
            request_url = END_POINT.format(app_url, exercise_id, ru_ref)
            auth = (basic_auth_username, basic_auth_password)
            response = requests.post(request_url, files=file, auth=auth)

            if response.status_code != 200:
                print('%% upload error "{}" - "{}"'.format(response.status_code, response.text))
                os.remove(file_name)
                exit(1)

            # A visual guide so the user knows something is uploading
            print(".", end='')
            sys.stdout.flush()

            # Removes the xls file created
            os.remove(file_name)


def create_xls_file(file_name, ru_ref):
    """
    Creates a xls file with data
    :param file_name: The file name of the xls
    :param ru_ref: The ru_ref, which is inserted into the xls document
    """

    workbook = xlsxwriter.Workbook(file_name)
    worksheet = workbook.add_worksheet()
    worksheet.set_column('A:A', 25)
    worksheet.write('A1', 'RU_REF = {}'.format(ru_ref))
    workbook.close()


if __name__ == '__main__':
    app_url = input('App URL (i.e http://localhost:8080): ')
    collection_exercise = input('Collection exercise id (i.e 14fb3e68-4dca-46db-bf49-04b84e07e77c):')
    basic_auth_username = input('Basic Auth username:')
    basic_auth_password = input('Basic Auth Password:')
    upload_test_collection_instruments(app_url, collection_exercise, basic_auth_username, basic_auth_password)
