Feature: Handle storing of Collection Instrument data


  Scenario: Post valid collection instrument
    Given a new collection instrument
    When a request is made to create the collection instrument
    Then the response status code is 201
    And the response returns the location for the data
    And the response returns an ETag
    And information is returned saying "item created"


  Scenario: Post invalid collection instrument data
    Given an incorrectly formed collection instrument
    When a request is made to create the collection instrument
    Then information is returned saying "invalid input, object invalid"
    And the response status code is 400


  @connect_to_database
  Scenario: Post collection instrument data that already exists
    Given a new collection instrument that already exists
    When a request is made to create the collection instrument
    Then information is returned saying "an existing item already exists"
    And the response status code is 409
