#!/bin/bash

chroot $1 mysqladmin create dashboard
svn export src $1/usr/local/share/archivematica-dashboard
