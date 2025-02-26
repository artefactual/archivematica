#!/bin/sh

test -e "$1" || exit 0
cp -R "$1" "$2"
