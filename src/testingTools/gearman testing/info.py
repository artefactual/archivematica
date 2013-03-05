#!/usr/bin/python -OO
import gearman
admin = gearman.admin_client.GearmanAdminClient(host_list=["localhost"])
admin.get_workers()
admin.get_status()
print "good"
