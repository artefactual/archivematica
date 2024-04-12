/*
Package controller provides the core Archivematica processing engine.

## Package

## Workflow

## Job

A job corresponds to a microservice (client script), a link in the workflow, and
the `Jobs` table in the database.

Types of jobs:
  - Decision jobs: outputDecisionJob, nextChainDecisionJob, updateContextDecisionJob.
  - Client jobs: directoryClientScriptJob, filesClientScriptJob, outputClientScriptJob
  - Local jobs: setUnitVarLinkJob, getUnitVarLinkJob

## Task

A task is a command passed to MCPClient for processing by client jobs.
*/
package controller
