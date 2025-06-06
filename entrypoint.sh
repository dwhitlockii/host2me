#!/bin/sh
set -e
MODE=${MODE:-web}
if [ "$MODE" = "pipeline" ]; then
    exec python run_full_pipeline.py
else
    exec python app.py
fi
