Feature: Handle adding a binary representation of Collection Instrument data

  @connect_to_database
  Scenario: Put collection instrument binary data by valid identifier
    Given a valid "Collection Instrument ID"
#    And an ETag for the collection instrument    # TODO: Should this test a cached ETag for HTTP header?
    And a binary collection instrument to add
    When a request is made to add the binary collection instrument
    Then information is returned saying "item updated"
    And the response status code is 201
    And the response returns an ETag


  @connect_to_database
  Scenario Outline: Put collection instrument binary data by incorrect identifier
    Given a "Collection Instrument ID" of "<identifier>"
    When a request is made for the collection instrument data
    Then information is returned saying "Invalid ID supplied"
    And the response status code is 400

 Examples: Incorrect domain name
        | identifier                          |
        | urn:ons.gov.us:id:ci:001.001.00001  |

    Examples: Incorrect number length
        | identifier                          |
        | urn:ons.gov.uk:id:ci:001.001.000000 |

    Examples: Incorrect type
        | identifier                          |
        | urn:ons.gov.uk:id:XX:001.001.00001  |

    Examples: Incorrect boundary value
        | identifier                                |
        | urn:ons.gov.uk:id:ci:-1000.-1000.-100000  |
        | urn:ons.gov.uk:id:ci:9999.9999.999999     |

    Examples: Collection instrument not found
        | identifier                          |
        | urn:ons.gov.uk:id:ci:000.000.00000  |
        | urn:ons.gov.uk:id:ci:999.999.99999  |


  @connect_to_database
  Scenario: Put collection instrument data binary data by invalid ETag
    Given a valid "Collection Instrument ID"
    And an invalid ETag
    When a request is made to add the binary collection instrument
    Then information is returned saying "Invalid ETag supplied"
    Then the response status code is 409
