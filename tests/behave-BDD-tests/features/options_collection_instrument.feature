Feature: Handle retrieval of options for Collection Instrument data

# ----------------------------------------------------------------------------------------------------------------------
# Collection Instrument options by valid identifier
# ----------------------------------------------------------------------------------------------------------------------
  @connect_to_database
  Scenario: Retrieve collection instrument options data by valid identifier
    Given a valid "Collection Instrument ID"
    When a request is made for the collection instrument options
    Then check the returned options are correct
    And the response status code is 200


# ----------------------------------------------------------------------------------------------------------------------
# Collection Instrument options by unknown identifier
# ----------------------------------------------------------------------------------------------------------------------
  @connect_to_database
  Scenario Outline: Get collection instrument data by incorrect identifier
    Given a "Collection Instrument ID" of "<identifier>"
    When a request is made for the collection instrument data
    Then information is returned saying "Collection instrument not found"
    And the response status code is 404

    Examples: Collection instrument options not found
        | identifier                          |
        | urn:ons.gov.uk:id:ci:000.000.00000  |
        | urn:ons.gov.uk:id:ci:999.999.99999  |
