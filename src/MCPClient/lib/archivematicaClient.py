#!/usr/bin/env python
import coverage
from client.mcp import main

if __name__ == "__main__":
    cov = coverage.Coverage(data_suffix=True)
    cov.start()
    main()
    cov.stop()
    cov.save()
