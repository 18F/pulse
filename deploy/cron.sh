#!/bin/bash

# Set the path to domain-scan.
export DOMAIN_SCAN_PATH=/opt/scan/domain-scan/scan
export DOMAIN_GATHER_PATH=/opt/scan/domain-scan/gather

# Baseline where Pulse is checked out to, what env we're using.
export PULSE_ENV=production
export PULSE_HOME=/opt/scan/pulse

# Go to pulse environment home
cd $PULSE_HOME

# Load environment
source $HOME/.bashrc

# Update one's own code (TODO: devops)
git pull

# run the relevant env-specific data update path
make update_$PULSE_ENV

# scan data was turned into db.json, and all data has been uploaded to S3.

# Finally, deploy the production website.
make cg_production_autodeploy
