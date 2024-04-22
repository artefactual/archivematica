# ccp

## Development environment

### Integration

ccp can be tested in isolation using the integration tests:

    go test -v ./integration/...

These are primarily used to build and test the workflow engine rewrite.

Things you should know about these tests:

- They don't depend on the services nor volumes provisioned by Docker Compose,
- They don't use the default Archivematica workflow,
- They don't dispatch jobs to MCPClient,
- They don't use Archivematica Storage Service.
- They use MySQL (using testcontainers) with a pre-made dump of the MCP db.

How to update the database dump:

1. Start the Archivematica development environment, and
2. Run:

      make dbdump | bzip2 --best > ccp/integration/mcp.sql.bz2

### Compose

Start the Archivematica development environment in the parent directory just
like you'd do in vanilla Archivematica. This fork has some Archivematica
services that are not part of the core removed to reduce its footprint:

- ElasticSearch (indexing disabled)
- ClamAV (virus scanning disabled)
- FITS (not a hard dependency)
- Gearman (provided by ccp)

Change the current directory to `hack/ccp` which hosts the Go project. Now:

1. Use `make push` to build ccp and run the containre within the environment.
2. Use `hack/transfer.sh` to submit a tiny transfer to the standard watched dir.
3. Watch the logs to see what's going on.
