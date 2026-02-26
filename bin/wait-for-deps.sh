#!/bin/bash

set -o errexit
set -o nounset

source $(dirname $0)/wait-for-postgres.sh

exec "$@"
