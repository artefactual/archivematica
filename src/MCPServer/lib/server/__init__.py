"""
MCPServer (Master Control Program Server) determines the jobs/tasks/microservices
run by Archivematica and arranges for their execution.

It makes use of the following major abstractions:
    * `workflow.Workflow` (and related classes `Link` and `Chain`) handle the workflow
      logic for Archivematica, described in workflow.json.
    * `jobs.base.Job` and subclasses handle execution of a single link of the workflow.
        * `jobs.client.ClientScriptJob` for jobs to be executed via MCPClient script
        * `jobs.client.DecisionJob` for workflow decision points
        * `jobs.client.LocalJob` for jobs that are executed on MCPServer directly
    * `jobs.chain.JobChain` handles passing context between jobs, and determining the
      next `Job` to be executed based on the workflow chain
    * `tasks.Task` corresponds to a single command to be executed by MCPClient
    * `tasks.backends.GearmanTaskBackend` handles passing tasks to MCPClient via
      gearman (in batches)
    * `packages.Package` subclasses `SIP`, `DIP`, and `Transfer` handle package
       related logic
    * a `concurrent.futures.ThreadPoolExecutor` handles out of process execution
    * `queues.PackageQueue` handles scheduling of `Job` objects for execution
      (throttled per package). The package queue is thread-safe.
    * `rpc_server.RPCServer` handles RPC requests from the dashboard, which arrive
      as gearman jobs.
"""
