echo "The default password is demo"

stty -echo
read -p "Enter mysql root password[hit Enter if blank]: " dpPassword; echo
stty echo

if [ -n "$dpPassword" ] ; then 
	dpPassword="-p${dpPassword}"
fi

cd postBuildRunAssistScripts
./preMCPLogging.sh "$dpPassword"
sudo mysqladmin create dcb $dpPassword
sudo mysqladmin create qubit $dpPassword
sudo mysqladmin create dashboard $dpPassword

dpPassword=""
