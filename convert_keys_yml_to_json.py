import json

import yaml


if __name__ == '__main__':
    with open("./test_keys/keys.yml") as fp:
        keys = yaml.safe_load(fp)

    with open("./test_keys/keys.json", "w") as fp:
        json.dump(keys, fp)
