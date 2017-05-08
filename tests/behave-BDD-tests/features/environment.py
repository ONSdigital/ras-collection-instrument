import psycopg2
import json


def before_feature(context, feature):
    """Set up context variables in Behave step files before a feature file is executed.
    
    :param context: Behave object used in scope of feature
    :param feature: Behave mandatory param
    :return: None
    """
    # Dev endpoint setup
    context.ci_domain = "http://127.0.0.1:"
    context.ci_port = "5052"

    # JWT setup
    valid_jwt = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54'
    context.valid_authorisation_header = {'authorization': valid_jwt}

    # Resources from app
    # TODO: Need an environment var to hold parent directory name/location
    context.resources_location = 'tests/behave-BDD-tests/features/resources/'

    with open('schema.json') as schema:
        context.schema_definition = json.load(schema)


def before_scenario(context, scenario):
    """Set up context variables in Behave step files before a scenario is executed.
    
    :param context: Behave object used in scope of scenario
    :param scenario: Behave mandatory param
    :return: None
    """
    if 'connect_to_database' in scenario.tags:
        # TODO: Need a startup / tear down of the db to run isolated tests against
        context.connection = psycopg2.connect(
            dbname='postgres',
            user='ras_collection_instrument',
            password='password',
            host='127.0.0.1',
            port='5431'
        )
        context.cursor = context.connection.cursor()


def after_scenario(context, scenario):
    """Tear down/rollback context variables and db transactions in Behave step files after a scenario is executed.
    
    :param context: Behave object used in scope of scenario
    :param scenario: Behave mandatory param
    :return: None
    """
    # TODO: Persistence problems for each scenario. Would it be best to drop/create entire db for startup/teardown instead?
    if 'connect_to_database' in scenario.tags:
        if context.failed:
            context.connection.rollback()
        context.connection.commit()
        context.connection.close()


# TODO: Could this be moved to before_scenario instead?
def before_step(context, step):
    """Set up context variables in Behave step files before a step is executed.
    
    :param context: Behave object used in scope of step
    :param step: Behave mandatory param
    :return: 
    """
    step_name = step.name
    if 'Collection Instrument ID' in step_name:
        context.db_table_column = 'urn'
        context.endpoint_parameter = '/id/'
        context.urn_id = 'ci'
    elif 'Survey ID' in step_name:
        context.db_table_column = 'survey_urn'
        context.endpoint_parameter = '/surveyid/'
        context.urn_id = 'surveyid'
    elif 'Reference' in step_name:
        context.db_table_column = 'content'
        context.db_row_content_key = 'reference'
        context.endpoint_parameter = '/reference/'
    elif 'Classifier' in step_name:
        context.db_table_column = 'content'
        context.db_row_content_key = 'classifiers'
        context.endpoint_parameter = '/?classifier='
