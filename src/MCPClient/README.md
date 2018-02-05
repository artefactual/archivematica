# MCPClient

This directory contains the Archivematica MCP client, frequently referred to as
`MCPClient`. Its main responsibility is to perform the tasks assigned by
`MCPServer`. These tasks are dispatched via Gearman. Technically speaking,
`MCPClient` is a pool of Gearman workers each one running in a separate thread.

The programs responsible of performing the Gearman jobs are contained in the
`lib/clientScripts/` directory. We frequently implement them as Python or Bash
scripts. When using Python, it's preferred to use the `logging` module - that
gives us the possibility to dispatch the log messages to more than one handler,
e.g. `stdout`, `stderr`, etc...
