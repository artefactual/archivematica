databaseName="MCP"
username="archivematica"
password="demo"
dpPassword="$1"
sudo mysqladmin create "$databaseName" $dpPassword
#sudo mysql $databaseName
sudo mysql $dpPassword --execute="source ../../../src/MCPServer/share/mysql" "$databaseName"
sudo mysql $dpPassword --execute="CREATE USER '${username}'@'localhost' IDENTIFIED BY '${password}'"
sudo mysql $dpPassword --execute="GRANT SELECT, UPDATE, INSERT, DELETE ON ${databaseName}.* TO '${username}'@'localhost'"


#to delete the database and all of it's contents
# sudo mysqladmin drop MCP
