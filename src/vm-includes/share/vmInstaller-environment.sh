#!/bin/bash

# This file is part of Archivematica.
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
# @subpackage Configuration
# @author Austin Trask <austin@artefactual.com>
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$

#Create DBs

if [ "$(id -u)" != "0" ]; then
	echo "Sorry, you are not root."
	exit 1
fi

echo "The default password is demo"

stty -echo
read -p "Enter mysql root password[hit Enter if blank]: " dpPassword; echo
stty echo

if [ -n "$dpPassword" ] ; then 
        dpPassword="-p${dpPassword}"
fi

includesDir="/usr/share/archivematica/vm-includes/"

${includesDir}vmInstaller-mcp-db.sh "$dpPassword"
mysqladmin create ica-atom $dpPassword
mysqladmin create dcb $dpPassword
mysqladmin create qubit $dpPassword
mysqladmin create dashboard $dpPassword

dpPassword=""

cp ${includesDir}php.ini /etc/php5/cli
cp ${includesDir}php.ini /etc/php5/apache2
cp ${includesDir}apache.default /etc/apache2/sites-available/default

export USER=$1

#Install externals/archivematica
mkdir -p /home/${USER}/Desktop
cp -a ${includesDir}Docs /home/${USER}/Docs
cp -a enviromentConfigFiles/exports /etc/exports
ln -s /home/${USER}/Docs /home/${USER}/Desktop


svn export http://archivematica.googlecode.com/svn/trunk/sampledata /usr/share/archivematica/sampleData
chown -R archivematica:archivematica /usr/share/archivematica/sampleData
#cp -a ${includesDir}postBuildScripts /home/${USER}/postBuildScripts

#XFCE configuration
mkdir /home/${USER}/.config
mkdir /home/${USER}/.config/Thunar
mkdir /home/${USER}/.config/autostart
mkdir -p /home/${USER}/.config/xfce4/desktop
mkdir -p /home/${USER}/.config/xfce4/panel

#add archivematica/dashboard icons
cp ${includesDir}desktopShortcuts/dashboard-desktop-icon.png /usr/share/icons
#cp ${includesDir}desktopShortcuts/dcb-desktop-icon.png /usr/share/icons
cp ${includesDir}desktopShortcuts/ica-atom-desktop-icon.png /usr/share/icons
cp ${includesDir}desktopShortcuts/archivematica-xubuntu-steel.png /usr/share/xfce4/backdrops/xubuntu-karmic.png
cp ${includesDir}desktopShortcuts/ica-atom.desktop /home/${USER}/Desktop
#cp ${includesDir}desktopShortcuts/dcb.desktop /home/${USER}/Desktop
cp ${includesDir}desktopShortcuts/dashboard.desktop /home/${USER}/Desktop
cp ${includesDir}desktopShortcuts/Terminal.desktop /home/${USER}/Desktop
cp ${includesDir}desktopShortcuts/vlc.desktop /home/${USER}/Desktop

#add launcher scripts
cp ${includesDir}desktopShortcuts/runica-atom.sh /usr/bin
#cp ${includesDir}desktopShortcuts/rundcb.sh /usr/bin
cp ${includesDir}desktopShortcuts/rundashboard.sh /usr/bin


#xfce4 configuration
cp ${includesDir}panel/* /home/${USER}/.config/xfce4/panel
cp ${includesDir}xfceCustomization/xfce4-desktop.xml /etc/xdg/xdg-xubuntu/xfce4/xfconf/xfce-perchannel-xml/
cp ${includesDir}xfceCustomization/xfce4-session.xml /etc/xdg/xdg-xubuntu/xfce4/xfconf/xfce-perchannel-xml/
cp ${includesDir}xfceCustomization/icons.screen0.rc /home/${USER}/.config/xfce4/desktop
cp ${includesDir}xfceCustomization/user-dirs.defaults /etc/xdg
#this is handled by /usr/share/archivematica/thunar-uca
#cp ${includesDir}xfceCustomization/uca.xml /home/${USER}/.config/Thunar
cp ${includesDir}xfceCustomization/thunarrc /home/${USER}/.config/Thunar
cp ${includesDir}xfceCustomization/thunar.desktop /home/${USER}/.config/autostart
cp ${includesDir}xfceCustomization/gtk-bookmarks /home/${USER}/.gtk-bookmarks
cp ${includesDir}xfceCustomization/gdm.custom.conf /etc/gdm/custom.conf

#fix permissions 
chmod 444 /home/${USER}/.config/xfce4/panel
chown -R ${USER}:${USER} /home/${USER}


${includesDir}vmInstaller-mcp-db.sh
${includesDir}vmInstaller-transcoder-db.sh
#${includesDir}vmInstaller-dcb.sh
${includesDir}vmInstaller-ica-atom.sh
#${includesDir}vmInstaller-qubit.sh

aptitude remove xscreensaver

#Get non-tainted sources.list
wget http://archivematica.org/downloads/sources.list -O /etc/apt/sources.list
aptitude update


gpasswd -a ${USER} archivematica
echo " "
echo "===PLEASE REBOOT TO ENABLE NEW GROUP SETTINGS==="
echo " "
sleep 3


#test
