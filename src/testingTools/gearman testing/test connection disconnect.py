#!/usr/bin/python -OO

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
# @subpackage Testing
# @author Joseph Perry <joseph@artefactual.com>


import gearman
import traceback
import threading
import sys
admin = gearman.admin_client.GearmanAdminClient(host_list=["localhost"])

def echo(gearman_worker, gearman_job):
    print gearman_job.data
    return gearman_job.data


#setup echo worker
gm_worker1 = gearman.GearmanWorker(["localhost"])
gm_worker1.register_task("echo", echo)
t = threading.Thread(target=gm_worker1.work)
t.daemon = True
t.start()


c=0
gm_client = gearman.GearmanClient(["localhost"])
try:
    for c in range(10000):
        request = gm_client.submit_job("echo", c.__str__())
    print "sleeping"
    while(1):
        import time
        time.sleep(3)
except Exception as inst:
    print >>sys.stderr, type(inst)     # the exception instance
    print >>sys.stderr, inst.args
    traceback.print_exc(file=sys.stdout)
    print "count: ", c
