Feature: Handle retrieval of Collection Instrument data

# This feature file is now more geared towards the more technical side of the testing (using URNs, HTTP status codes
# etc). These URNs & codes could be moved to the steps implementation instead, so that this feature remains more high level.

  # TODO: Need to add a background step here to ensure the service is running before each scenario is executed by checking the end point e.g. http://localhost:8070/servicestatus

  @connect_to_database
  Scenario: Get all available collection instrument data
    Given one or more collection instruments exist
    When a request is made for one or more collection instrument data
    Then check the returned data are correct
    And the response status code is 200

  #TODO: searchString, skip (pagination), and limit records test to go here!


  @connect_to_database
  Scenario Outline: Get collection instrument data by valid identifier
    Given a valid <identifier_type>
    When a request is made for the collection instrument data
    Then check the returned data are correct
    And the response status code is 200
    And the response returns an ETag

    Examples:
        | identifier_type           |
        | Collection Instrument ID  |
        | Survey ID                 |
        | Reference                 |
        | Classifier                |


  @connect_to_database
  Scenario Outline: Get collection instrument data by incorrect identifier
    Given a <identifier_type> of "<identifier>"
    When a request is made for the collection instrument data
    Then information is returned saying "<text>"
    And the response status code is <status_code>

    Examples: Incorrect domain name
        | identifier_type           | identifier                                    | text                            | status_code |
        | Collection Instrument ID  | urn:ons.gov.us:id:ci:001.001.00001            | Invalid ID supplied             | 400         |
        | Survey ID                 | urn:ons.gov.us:id:survey:001.001.00001        | Invalid ID supplied             | 400         |

    Examples: Incorrect number length
        | identifier_type           | identifier                                    | text                            | status_code |
        | Collection Instrument ID  | urn:ons.gov.uk:id:ci:001.001.000000           | Invalid ID supplied             | 400         |
        | Survey ID                 | urn:ons.gov.us:id:survey:001.001.00001        | Invalid ID supplied             | 400         |

    Examples: Incorrect type
        | identifier_type           | identifier                                    | text                            | status_code |
        | Collection Instrument ID  | urn:ons.gov.uk:id:XX:001.001.00001            | Invalid ID supplied             | 400         |
        | Survey ID                 | urn:ons.gov.uk:id:XX:001.001.00001            | Invalid ID supplied             | 400         |
        | Classifier                | 'TEST_MALFORMED_CLASSIFIER':'ABC'             | Bad input parameter             | 400         |

    Examples: Incorrect boundary value
        | identifier_type           | identifier                                    | text                            | status_code |
        | Collection Instrument ID  | urn:ons.gov.uk:id:ci:-1000.-1000.-100000      | Invalid ID supplied             | 400         |
        | Collection Instrument ID  | urn:ons.gov.uk:id:ci:9999.9999.999999         | Invalid ID supplied             | 400         |
        | Survey ID                 | urn:ons.gov.uk:id:survey:-1000.-1000.-100000  | Invalid ID supplied             | 400         |
        | Survey ID                 | urn:ons.gov.uk:id:survey:9999.9999.999999     | Invalid ID supplied             | 400         |

    Examples: Collection instrument not found
        | identifier_type           | identifier                                    | text                            | status_code |
        | Collection Instrument ID  | urn:ons.gov.uk:id:ci:000.000.00000            | Collection instrument not found | 404         |
        | Collection Instrument ID  | urn:ons.gov.uk:id:ci:999.999.99999            | Collection instrument not found | 404         |
        | Survey ID                 | urn:ons.gov.uk:id:survey:000.000.00000        | Collection instrument not found | 404         |
        | Survey ID                 | urn:ons.gov.uk:id:survey:999.999.99999        | Collection instrument not found | 404         |
        | Reference                 | bdd-test-reference                            | Collection instrument not found | 404         |
        | Classifier                | {'TEST_UNKNOWN_CLASSIFIER_NAME':'ABC'}        | Collection instrument not found | 404         |


  @connect_to_database
  Scenario Outline: Get collection instrument data end-to-end
    Given a new collection instrument has been created
    And the <identifier_type> of the new collection instrument
    When a request is made for the collection instrument data
    Then check the returned data are correct
    And the response status code is 200
    And the response returns an ETag
    When the new collection instrument has been removed
    And a request is made for the collection instrument data
    Then information is returned saying "Collection instrument not found"
    And the response status code is 404

    Examples:
      | identifier_type           |
      | Collection Instrument ID  |
      | Survey ID                 |
      | Reference                 |
      | Classifier                |


  @connect_to_database
  Scenario: Get collection instrument file by valid identifier end-to-end
    Given a valid "Collection Instrument ID"
#    And an ETag for the collection instrument    # TODO: Should this test a cached ETag for HTTP header?
    And a binary collection instrument to add
    When a request is made to add the binary collection instrument
    Then information is returned saying "item updated"
    And the response status code is 201
    And the response returns an ETag
    When a request is made for the collection instrument file
    Then the response status code is 200
    And the response returns an ETag
    And the returned binary collection instrument matches the file that was added
