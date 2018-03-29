# MCPClient

This directory contains the Archivematica MCP client, frequently referred to as
`MCPClient`. Its main responsibility is to perform the tasks assigned by
`MCPServer`. These tasks are dispatched via Gearman.

The programs responsible for performing the Gearman jobs are contained in the
`lib/clientScripts/` directory. Each program is a Python module that
implements the following function:

    def call(jobs)

The `jobs` parameter is an array of `Job` objects, each corresponding
to a task to be performed. If there are arguments associated with the
task, `job.args` will hold those. When each job is run, it is
expected to produce an exit code along with output and error
streams. You set the exit code for a job with:

    job.set_status(int)

To record standard output and standard error, there are several
methods: write_* for storing literal strings; print_* for storing
literal strings with newlines added; pyprint for a Python
`print`-compatible API. See the Job class for more information on
these.

There are numerous examples of client scripts in the `clientScripts`
directory. Commonly they will follow a pattern like:

    from custom_handlers import get_script_logger
    # ...
    logger = get_script_logger("archivematica.mcp.client.myModuleName")

    # ...

    def call(jobs):
        with transaction.atomic():
            for job in jobs:
                with job.JobContext(logger=logger):
                    result = process_job(job.args)
                    job.set_status(result)

Some notable features:

  * Where the task will insert/update/delete rows from the database,
    we wrap it in a transaction. Besides providing atomicity if
    something goes wrong, this also boosts performance significantly.

  * Generally we iterate over each job one-by-one, although nothing
    stops you from working in larger batches if that suits.

  * `JobContext` is a convenience class that executes its body in a
    modified context:

      - Any uncaught exceptions will be logged as standard error
        output, and the job's status will be set to 1.

      - If you supply the `logger` keyword, your global logger will be
        configured to send its output to the job's standard error
        stream.

## Concurrency

Some tasks benefit from running multiple processes at once--giving
better throughput. To instruct MCPClient to run your task in multiple
concurrent processes, provide a function in your module as follows:

    import multiprocessing
    def concurrent_instances():
        return multiprocessing.cpu_count()

when your task includes `concurrent_instances`, MCPClient will call
that to determine how many instances to run (at the time of writing,
we just default to running as many processes as you have CPUs, but it
might make sense to run fewer or more in some cases).  Each instance
will be run in its own Python subprocess with a subset of the total
jobs.

Besides the method definition, that's all you need to do to run
concurrently: MCPClient takes care of creating the subprocesses,
dividing up the work and gathering everything up at the end.
