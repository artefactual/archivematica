#!/bin/bash

set -e

target="$1"
if [ -e "${target}" ]; then
	sudo chown -R archivematica:archivematica "${target}"  
	echo `basename "${target}"` owned by "archivematica:archivematica" now 
	sudo chmod -R 660 "${target}"
	sudo chmod 640 "${target}"
    sudo find "${target}" -type d -execdir chmod 770 '{}' +
	if [ -d "${target}objects" ]; then	
		sudo chmod -R 660 "${target}objects"
        sudo find "${target}objects" -type d -execdir chmod 770 '{}' +
	fi
	if [ -d "${target}metadata" ]; then	
		sudo chmod -R 660 "${target}metadata"
        sudo find "${target}metadata" -type d -execdir chmod 770 '{}' +
	fi
else
  	echo $target does not exist\ 1>&2
  	exit 1 
fi

