#!/bin/bash

# Set the path to domain-scan.
export DOMAIN_SCAN_PATH=/opt/scan/domain-scan/scan

# go to pulse environment home
cd $HOME/pulse/$PULSE_ENV/current

# load virtualenv
source $HOME/.virtualenvs/pulse-$PULSE_ENV/bin/activate

# run the relevant env-specific data update path
make update_$PULSE_ENV
