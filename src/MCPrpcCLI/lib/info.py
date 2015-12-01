#!/usr/bin/env python2

import gearman
admin = gearman.admin_client.GearmanAdminClient(host_list=["127.0.0.1"])
#print admin.get_status()
#print admin.get_workers()

for client in admin.get_workers():
    if client["client_id"] != "-": #exclude server task connections
        print client["client_id"], client["ip"]

for stat in admin.get_status():
    if stat["running"] != 0 or stat["queued"] != 0:
        print stat
