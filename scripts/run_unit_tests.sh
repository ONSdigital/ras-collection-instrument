set -o pipefail
py.test --cov=swagger_server --cov-report xml
