#!/usr/bin/bash

set -e


INPUT_DIR="/home/martin/data/sealoc_camera_tables/"
DATABASE_URL="sqlite:////home/martin/data/sealoc_camera_tables/sealoc.db"

if true; then
  uv run sealoc tasks init-database \
      --database-url "${DATABASE_URL}" \
      --clear
fi

uv run sealoc tasks populate-database \
    --database-url "${DATABASE_URL}" \
    --input-dir "${INPUT_DIR}"
