#!/usr/bin/env python2

"""
Manages the interactions between the MCP Server and the MCP Client (via
Gearman).

The big idea:

  * Any MCP Server thread wanting to run an MCP Client task calls
    TaskGroupRunner.runTaskGroup(), supplying the task group to run and a
    callback.  This call returns immediately.

  * Behind the scenes, TaskGroupRunner runs a background thread that takes care
    of scheduling task groups to be run and tracking the status of currently
    executing Gearman requests.  As jobs finish, their callbacks are fired.
"""

# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.

# @package Archivematica
# @subpackage MCPServer

import threading
import gearman
import cPickle
import logging
import time
import traceback
import collections

from multiprocessing.pool import ThreadPool

from django.conf import settings as django_settings

LOGGER = logging.getLogger('archivematica.mcp.server')


class TaskGroupRunner():

    # How often our background thread will wake up and do its thing
    POLL_DELAY_SECONDS = 0.2

    # The frequency with which we'll log task stats
    NOTIFICATION_INTERVAL_SECONDS = 10

    # Our singleton instance
    _instance = None

    # A TaskGroupJob is just a TaskGroup we've been asked to run, plus its
    # associated callback
    #
    # (not to be confused with a Gearman Job, which is a handle to a task
    # Gearman is currently handling for us...)
    TaskGroupJob = collections.namedtuple('Job', ['task_group', 'finished_callback'])

    @staticmethod
    def _init():
        """
        Create a singleton instance of our TaskGroupRunner and start its poll
        thread.
        """

        TaskGroupRunner._instance = TaskGroupRunner()
        TaskGroupRunner._instance._start_polling()

    @staticmethod
    def runTaskGroup(task_group, finished_callback):
        """
        Submit a task group to be run.  Call `finished_callback` when it completes.
        """
        TaskGroupRunner._instance.submit(TaskGroupRunner.TaskGroupJob(task_group, finished_callback))

    def __init__(self):
        # The list of TaskGroups that are ready to run but not yet submitted to
        # the MCP Client.
        self.pending_task_group_jobs_lock = threading.Lock()
        self.pending_task_group_jobs = []

        # Gearman jobs that are currently waiting on the MCP Client
        self.running_gearman_jobs = []
        self.task_group_jobs_by_uuid = {}

        # Used to run completed callbacks off the main thread.
        self.pool = ThreadPool(django_settings.LIMIT_TASK_THREADS)

        # Our background thread (created by _start_polling)
        self.poll_thread = None

        # The time we last printed some diagnostics
        self.last_notification_time = 0

    def submit(self, task_group_job):
        """
        Record a TaskGroupJob that is ready to run.
        """
        with self.pending_task_group_jobs_lock:
            self.pending_task_group_jobs.append(task_group_job)

    def _start_polling(self):
        """
        Start an event loop that will submit TaskGroups to MCP Client and monitor
        the status of running Gearman jobs.
        """
        def event_loop():
            gm_client = gearman.GearmanClient([django_settings.GEARMAN_SERVER])

            while True:
                try:
                    time.sleep(TaskGroupRunner.POLL_DELAY_SECONDS)
                    self._poll(gm_client)
                except Exception as e:
                    LOGGER.error("\n\n*** Uncaught error in event loop: " + str(e) + ": " + str(type(e)))
                    LOGGER.exception(traceback)
                    LOGGER.error("\n\n\n")
                    time.sleep(5)

        self.poll_thread = threading.Thread(target=event_loop)
        self.poll_thread.start()

    def _finish_task_group_job(self, task_group_job):
        """
        Fire the finished callback for a completed TaskGroupJob.
        """
        try:
            task_group_job.finished_callback(task_group_job.task_group)
        except Exception as e:
            LOGGER.error("Finish callback failed: " + str(e))
            LOGGER.exception(e)

    def _poll(self, gm_client):
        """
        Run a single poll loop (get new jobs, monitor running ones).
        """
        self._submit_pending_task_group_jobs(gm_client)
        self._monitor_running_jobs(gm_client)

    def _submit_pending_task_group_jobs(self, gm_client):
        # Snapshot and clear the current list of pending TaskGroups
        pending_task_group_jobs = None
        with self.pending_task_group_jobs_lock:
            pending_task_group_jobs = list(self.pending_task_group_jobs)
            self.pending_task_group_jobs = []

        # ... and send them off
        for task_group_job in pending_task_group_jobs:
            task_group = task_group_job.task_group
            self.task_group_jobs_by_uuid[task_group.UUID] = task_group_job

            job_request = None
            while job_request is None:
                try:
                    job_request = gm_client.submit_job(
                        task=task_group.name(),
                        data=task_group.serialize(),
                        unique=task_group.UUID,
                        wait_until_complete=False,
                        background=False,
                        max_retries=10)
                except Exception as e:
                    LOGGER.warning("Retrying submit for job %s...: %s: %s" % (task_group.UUID, str(e), str(type(e))))
                    LOGGER.exception(e)
                    time.sleep(5)

                self.running_gearman_jobs.append(job_request)

    def _monitor_running_jobs(self, gm_client):
        statuses = []
        for job in self.running_gearman_jobs:
            try:
                status = gm_client.get_job_status(job)
                statuses.append(status)
            except KeyError:
                # There seems to be a race condition here in the Gearman client.
                # If the job finishes before we get a chance to poll for its
                # status, a KeyError is thrown.
                #
                # Not a huge problem: we can just try again on the next poll.
                #
                statuses.append(job)

        finished_jobs = [job for job in statuses if job.complete]
        still_running_jobs = [job for job in statuses if not job.complete]

        # Record the jobs that are still running.  We do this here (instead of
        # after dealing with the jobs that have finished) because it ensures we
        # don't get stuck.  I.e. if processing the first finished job in the
        # list throws an exception for some reason, we would never progress past
        # that point.
        #
        # By clearing those finished jobs out of `running_gearman_jobs`, we
        # would just skip over them and keep on trucking.
        self.running_gearman_jobs = still_running_jobs

        # Populate each task's results with what we got back from the MCP Client.
        for finished_job in finished_jobs:
            self._handle_gearman_response(finished_job)

        for finished_job in finished_jobs:
            task_group_job = self.task_group_jobs_by_uuid.pop(finished_job.gearman_job.unique)
            self.pool.apply_async(self._finish_task_group_job, [task_group_job])

        now = time.time()
        if (now - self.last_notification_time) > TaskGroupRunner.NOTIFICATION_INTERVAL_SECONDS:
            LOGGER.info("%d jobs pending; %d jobs running; %d known task groups",
                        len(self.pending_task_group_jobs),
                        len(self.running_gearman_jobs),
                        len(self.task_group_jobs_by_uuid))
            self.last_notification_time = now

    def _handle_gearman_response(self, job_request):
        """
        MCP Client will return a map like:

             {'task_results':
               {'task_1_uuid': {'exitCode': 0, 'exitStatus': 'OK', ...}},
               {'task_2_uuid': {'exitCode': 1, 'exitStatus': 'ERROR', ...}},
             }

        Here we parse that, map each entry back to its task within the TaskGroup
        and update its value.
        """
        if job_request.gearman_job.unique not in self.task_group_jobs_by_uuid:
            LOGGER.error("Couldn't find task group '%s' in the list of running jobs", job_request.gearman_job.unique)
            return

        task_group_job = self.task_group_jobs_by_uuid[job_request.gearman_job.unique]
        task_group = task_group_job.task_group

        if job_request.complete:
            # The job completed successfully
            if job_request.result is None:
                LOGGER.debug("Expected a map containing 'task_results', but got None")
                LOGGER.debug("Task was: %s", task_group.serialize())
                return

            job_result = cPickle.loads(job_request.result)

            if 'task_results' not in job_result:
                LOGGER.debug("Expected a map containing 'task_results', but got: %s" % (job_result))
                return

            task_results = job_result['task_results']

            for task in task_group.tasks():
                result = task_results.get(task.UUID, None)

                if result is None:
                    LOGGER.debug("Warning: Couldn't find a task with UUID: %s in our results" % (task.UUID))
                    continue

                task.results['exitCode'] = result['exitCode']
                task.results['exitStatus'] = result.get('exitStatus', '')
                task.results['stdout'] = result.get('stdout', '')
                task.results['stderr'] = result.get('stderr', '')

                LOGGER.debug('Task %s finished! Result %s - %s', job_request.job.unique, job_request.state, result['exitCode'])
        else:
            # If the entire task failed, we'll propagate the failure to all tasks in the batch.
            msg = ""

            if job_request.timed_out:
                msg = 'Task %s timed out!' % (job_request.unique)
            elif job_request.state == gearman.client.JOB_UNKNOWN:
                msg = 'Task %s connection failed!' % (job_request.unique)
            else:
                msg = 'Task %s failed!' % (job_request.unique)

            LOGGER.error(msg)
            for task in task_group.tasks():
                task.results['exitCode'] = 1


TaskGroupRunner._init()
