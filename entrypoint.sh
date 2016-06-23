#!/bin/bash

if [ -n "$LOOP_SECONDS" ]; then
    while true; do
        $@
        sleep $LOOP_SECONDS
    done
else
    $@
fi
