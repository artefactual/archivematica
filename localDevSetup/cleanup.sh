#!/bin/bash

# this loop is required because we need to leave storage service files alone
dirs=("/usr/lib/archivematica" "/etc/archivematica" "/usr/share/archivematica" "/var/archivematica")
for dir in ${dirs[@]} 
do
    if [ "$(ls -A $dir)" ]; then
        find $dir -type l | while read file ; do
            if [[ ! ${file} =~ "storage" ]]; then
                sudo rm ${file}
            fi
        done
        if  [ ! "$(ls -A $dir)" ]; then
            sudo rmdir $dir 
        fi
    fi
done

sudo rm /etc/apache2/sites-enabled/000-default.conf
