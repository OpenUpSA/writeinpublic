#!/bin/bash

set -o errexit
set -o nounset

source $(dirname $0)/wait-for-postgres.sh
source $(dirname $0)/wait-for-elasticsearch.sh

python /app/patch_packages.py

exec "$@"
