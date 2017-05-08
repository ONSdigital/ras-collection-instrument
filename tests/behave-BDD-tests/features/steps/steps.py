"""
This steps file holds common steps used for testing of GET / POST / PUT etc. end points.

Most of the context variables in this file are set up in environment.py.
"""
# TODO: Check content-type assertions. Should these all be in the format of 'application/vnd.ons.<type>'?

import os.path
import ast

from psycopg2 import IntegrityError
from psycopg2.extensions import AsIs
import jsonschema
import requests
from behave import given, then, when


# ----------------------------------------------------------------------------------------------------------------------
# Common 'given' steps
# ----------------------------------------------------------------------------------------------------------------------
@given('the {identifier_type} of the new collection instrument')
def step_impl(context, identifier_type):
    sql_body = """
        SELECT %s
        FROM ras_collection_instrument.ras_collection_instruments
        ORDER BY %s DESC
        LIMIT 1;
    """
    col = AsIs(context.db_table_column)
    context.cursor.execute(sql_body, (col, col))
    content_row = context.cursor.fetchone()

    if isinstance(content_row[0], str):
        context.identifier = content_row[0]
    else:
        context.identifier = str(content_row[0][context.db_row_content_key])


@given('a {identifier_type} of "{identifier}"')
def step_impl(context, identifier_type, identifier):
    context.identifier = identifier


@given('a valid {identifier_type}')
def step_impl(context, identifier_type):
    sql_body = """
        SELECT %s
        FROM ras_collection_instrument.ras_collection_instruments
        LIMIT 1;
    """
    col = AsIs(context.db_table_column)
    context.cursor.execute(sql_body, (col,))
    context.content_row = context.cursor.fetchone()

    if isinstance(context.content_row[0], str):
        context.identifier = context.content_row[0]
    else:
        context.identifier = str(context.content_row[0][context.db_row_content_key])


@given('a new collection instrument has been created')
def step_impl(context):
    # TODO: Instead of wrapping this in try/except, could we just rollback in environment.py if error was encountered?
    try:
        context.cursor.execute(open(context.resources_location + 'bdd_insert_collection_instrument.sql', 'r').read())
        context.connection.commit()
    except IntegrityError:
        print(
            "INFO: Record already exists in db. Possibly caused by a previous step failing and connection not rolling back.")
        context.connection.rollback()
        return
    assert context.cursor.rowcount > 0


@given('one or more collection instruments exist')
def step_impl(context):
    sql_body = """
        SELECT EXISTS (
            SELECT *
            FROM ras_collection_instrument.ras_collection_instruments
        )
    """
    context.cursor.execute(sql_body, )
    identifier_exists = context.cursor.fetchone()[0]
    assert identifier_exists is True


@given('a new collection instrument')
def step_impl(context):
    context.new_ci = {
        "reference": "test-post-collection-instrument",
        "surveyId": "urn:ons.gov.uk:id:survey:001.234.56789",
        "id": "urn:ons.gov.uk:id:ci:001.234.56789",
        "ciType": "OFFLINE",
        "classifiers": {
            "RU_REF": "1731"
        }
    }


@given('an incorrectly formed collection instrument')
def step_impl(context):
    context.new_ci = [{
        "test-key": "test"
    }]


@given('a new collection instrument that already exists')
def step_impl(context):
    context.execute_steps('''
        given a new collection instrument
        when a request is made to create the collection instrument
    ''')


@given('a binary collection instrument to add')
def step_impl(context):
    context.test_file = context.resources_location + 'bdd_test_file_for_http_put_method.txt'
    assert os.path.exists(context.test_file)


@given('an invalid ETag')
def step_impl(context):
    raise NotImplementedError('STEP: Given an invalid ETag. ETag not currently stored.')


# ----------------------------------------------------------------------------------------------------------------------
# 'when' steps
# ----------------------------------------------------------------------------------------------------------------------
@when('a request is made for the collection instrument data')
def step_impl(context):
    ci_endpoint = "/collectioninstrument" + context.endpoint_parameter
    url = context.ci_domain + context.ci_port + ci_endpoint + context.identifier
    context.response = requests.get(url, headers=context.valid_authorisation_header)
    print(url)


# TODO: This is very similar to "a request is made for the collection instrument data".
@when('a request is made for one or more collection instrument data')
def step_impl(context):
    ci_endpoint = "/collectioninstrument"
    url = context.ci_domain + context.ci_port + ci_endpoint
    context.response = requests.get(url, headers=context.valid_authorisation_header)
    print(url)


# TODO: This is very similar to "a request is made for the collection instrument data".
@when('a request is made for the collection instrument options')
def step_impl(context):
    ci_endpoint = "/collectioninstrument" + context.endpoint_parameter
    url = context.ci_domain + context.ci_port + ci_endpoint + context.identifier
    context.response = requests.options(url, headers=context.valid_authorisation_header)
    print(url)


@when('a request is made to create the collection instrument')
def step_impl(context):
    ci_endpoint = "/collectioninstrument/"
    url = context.ci_domain + context.ci_port + ci_endpoint
    context.response = requests.post(
        url,
        json=context.new_ci,
        headers=context.valid_authorisation_header
    )
    print(url)


@when('a request is made to add the binary collection instrument')
def step_impl(context):
    ci_endpoint = "/collectioninstrument" + context.endpoint_parameter
    url = context.ci_domain + context.ci_port + ci_endpoint + context.identifier

    with open(context.test_file, 'rb') as test_file:
        requests.put(
            url,
            headers=context.valid_authorisation_header,
            files={'fileupload': test_file}
        )
    print(url)


@when('the new collection instrument has been removed')
def step_impl(context):
    delete_body = """
        DELETE FROM ras_collection_instrument.ras_collection_instruments
        WHERE %s = %s;
        """
    col = AsIs(context.db_table_column)
    context.cursor.execute(delete_body, (col, context.identifier))
    context.connection.commit() if context.cursor.rowcount == 1 else context.connection.rollback()
    assert context.cursor.rowcount == 1


@when('a request is made for the collection instrument file')
def step_impl(context):
    raise NotImplementedError('STEP: When a request is made for the collection instrument file')


# ----------------------------------------------------------------------------------------------------------------------
# Common 'then' steps
# ----------------------------------------------------------------------------------------------------------------------
@then('the response status code is {status_code}')
def step_impl(context, status_code):
    assert context.response.status_code == int(status_code)


@then('the response returns an ETag')
def step_impl(context):
    assert len(context.response.headers['ETag']) > 0  # TODO: Improve this assertion?


@then('information is returned saying "{text}"')
def step_impl(context, text):
    print("Expected text is: " + text)
    assert context.response.text == text
    assert context.response.headers['Content-Type'] == 'text/html; charset=utf-8'


@then('check the returned data are correct')
def step_impl(context):
    assert context.response.headers['Content-Type'] == 'collection+json'
    context.response_text = ast.literal_eval(context.response.text)

    if isinstance(context.response_text, list):
        for row in context.response_text:
            jsonschema.validate(row, context.schema_definition)
    else:
        jsonschema.validate(context.response_text, context.schema_definition)


@then('check the returned options are correct')
def step_impl(context):
    assert context.response.headers['Content-Type'] == 'collection+json'
    response_json = ast.literal_eval(context.response.text)
    assert 'representation options' in response_json


@then('the collection instrument is created successfully')
def step_impl(context):
    assert context.response.text == 'item created'


@then('the response returns the location for the data')
def step_impl(context):
    assert context.ci_domain + context.ci_port in context.response.headers['Location']  #TODO: Improve this assertion


@then('the returned binary collection instrument matches the file that was added')
def step_impl(context):
    raise NotImplementedError('STEP: Then the returned binary collection instrument matches the file that was added')
