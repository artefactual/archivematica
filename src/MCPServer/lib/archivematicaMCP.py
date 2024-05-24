#!/usr/bin/env python
import coverage
from server.mcp import main

# TODO: update the entrypoint and remove this alias
cov = coverage.Coverage(data_suffix=True)
cov.start()
main()
cov.stop()
cov.save()
