#!/bin/bash

sudo chown -R archivematica:archivematica "$2"
touch "$2"
chmod -R "$1" "$2"
