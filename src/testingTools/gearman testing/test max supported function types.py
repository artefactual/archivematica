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
import uuid
import traceback
import threading
import sys
admin = gearman.admin_client.GearmanAdminClient(host_list=["localhost"])

def allcalls(gearman_worker, gearman_job):
    pass

gm_worker1 = gearman.GearmanWorker(["localhost"])
gm_worker2 = gearman.GearmanWorker(["localhost"])
gm_worker3 = gearman.GearmanWorker(["localhost"])
gm_worker4 = gearman.GearmanWorker(["localhost"])

c=0
try:
    for c in range(700):
        #key = c.__str__()
        key = uuid.uuid4().__str__()#[:10]
        gm_worker1.register_task(key, allcalls)
        gm_worker2.register_task(key, allcalls)
        gm_worker3.register_task(key, allcalls)
        gm_worker4.register_task(key, allcalls)
        admin.get_workers()
        admin.get_status()
        print c 
    
    #start the workers
    for worker in [gm_worker1, gm_worker2, gm_worker3, gm_worker4]:
        t = threading.Thread(target=worker.work)
        t.daemon = True
        t.start()
        
    #print admin.get_workers()
    #print admin.get_status()
    print "sleeping"
    while(1):
        import time
        time.sleep(3)
except Exception as inst:
    print >>sys.stderr, type(inst)     # the exception instance
    print >>sys.stderr, inst.args
    traceback.print_exc(file=sys.stdout)
    print "count: ", c
