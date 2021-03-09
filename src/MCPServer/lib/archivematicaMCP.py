#!/usr/bin/env python2
import atexit

from server.mcp import main
import coverage

cov = coverage.Coverage(data_file="/src/cov/.coverage", data_suffix=True)
cov.start()


def save_coverage():
    cov.stop()
    cov.save()


atexit.register(save_coverage)

# TODO: update the entrypoint and remove this alias
main()
