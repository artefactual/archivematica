if [ ! -f  /usr/bin/dot ]; then
   sudo apt-get install graphviz
fi
rm ./*.png
set -e
./main.py
java -jar ./../../../archivematicaCommon/lib/externals/plantUML/plantuml.jar ./plantUML.txt 
ls


