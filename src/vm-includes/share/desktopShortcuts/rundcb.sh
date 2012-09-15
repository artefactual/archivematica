#!/bin/bash
find ~/.mozilla -name extensions.cache -exec rm -f {} \; && firefox http://localhost/dcb
