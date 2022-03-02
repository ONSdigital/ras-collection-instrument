import sys

import requests
from requests.exceptions import HTTPError

# Run this script by doing `pipenv run python scripts/migrate_instruments_to_gcp.py`

# Populate this with the instrument ids you wish to migrate
instrument_ids = []

print("Beginning migrating instruments")

for instrument_id in instrument_ids:
    print(f"Migrating instrument [{instrument_id}")
    # If you're port forwarding, this should remain the same regardless of environment
    url = f"http://localhost:8002/collection-instrument-api/1.0.2/migrate/{instrument_id}"

    # Update this depending on what environment you're running this script against
    auth = ("admin", "secret")
    response = requests.get(url, auth=auth)
    try:
        response.raise_for_status()
    except HTTPError:
        print(f"Something went wrong migrating instrument with id [{instrument_id}], please investigate")
        print("--------")
        print(response.json())
        print(response.status_code)
        print("--------")
        sys.exit(1)

    print(f"Successfully migrated instrument with id [{instrument_id}]")

print("Finished migrating instruments")

