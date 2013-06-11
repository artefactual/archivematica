#!/usr/bin/python

# author: jhs
# created: 2013-01-28
# project: Rockefeller Archivematica - Archivists Toolkit Integration

# notes: this script creates a sql script, that can be run against an AT database
#        it will insert digital object records into AT for existing Archival Descriptions objects
#
# inputs:  requires information about the AT database, and the location of the DIP, plus some metadata supplied by the user
#
# first version of this script gets the input from prompts, next version will get it from MCP db.
# 
# example usage:
#
# python at_import.py --host=localhost --port=3306 --dbname="ATTEST" --dbuser=ATuser --dbpass=hello --dip_location="/home/jhs/dip" --dip_name=mydip --atuser=myuser --use_statement="Image-Service" --uri_prefix="http://www.rockarch.org/" 
#

import os
import sys
import MySQLdb
from time import localtime, strftime
import argparse
import logging
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import archivistsToolkit.atk as atk
import mets

#global variables
db = None
cursor = None
testMode =0 
base_fv_id = 1

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
#logger.addHandler(logging.FileHandler('at_upload.log', mode='a'))


    
def recursive_file_gen(mydir):
    for root, dirs, files in os.walk(mydir):
        for file in files:
            yield os.path.join(root, file)


def process_sql(str):
    global cursor 
    if testMode:
        print str
    else:
        cursor.execute(str)            
        newID = cursor.lastrowid
        return newID

def get_user_input():
    print "Archivematica import to AT script"
    print "Welcome\n"
    atdbhost = raw_input("AT database hostname:")
    atdbport = raw_input("AT database port:")
    atdbuser = raw_input("AT database user name:")
    atpass = raw_input("AT database user password:")
    atuser = raw_input("AT username:")
    atdb = raw_input("AT database name:")

    dip_location = raw_input("Location of DIP:")
    dip_name = raw_input("Name of DIP:")

    object_type = raw_input("Object Type:")
    ead_actuate = raw_input("EAD Actuate:")
    ead_show = raw_input("EAD Show:")
    use_statement = raw_input("Use Statement:")

    uri_prefix = raw_input("prefix for uri:")
    #aip = raw_input("Name of mets file:")
    #fileName = raw_input("File name:")
    return atdbhost, atdbport, atdbuser, atpass, atdb, dip_location, dip_name, atuser, object_type, ead_actuate, ead_show, use_statement, uri_prefix


def get_files_from_dip(dip_location, dip_name, dip_uuid):
    #need to find files in objects dir of dip:
    # go to dipLocation/dipName/objects
    # get a directory listing
    # for each item, set fileName and go
    try:
        mydir = dip_location + "objects/"
        mylist = list(recursive_file_gen(mydir))
        
        if len(mylist) > 0:
            return mylist
        else:
            logger.error("no files in " + mydir)
            raise ValueError("cannot find dip")
            exit(2)
    except Exception:
        raise
        exit(3)

def upload_to_atk(mylist, atuser, ead_actuate, ead_show, object_type, use_statement, uri_prefix, dip_uuid, access_conditions, use_conditions, restrictions, dip_location):
    #get mets object if needed
    mets_file = None
    mymets = None
    if restrictions == 'premis' or len(access_conditions) == 0:
        try:
            dip_file = dip_location + 'METS.' + dip_uuid + '.xml'
            mets_file = mets.MetsFile(dip_file)
            mets_file.parse()
            mymets = mets_file.mets
        except Exception:
            raise
            exit(4)
            
    global db
    global cursor
    db = atk.connect_db(args.atdbhost, args.atdbport, args.atdbuser, args.atdbpass, args.atdb)
    cursor = db.cursor()
    sql0 = "select max(fileVersionId) from FileVersions"
    logger.debug('sql0: ' + sql0)
    cursor.execute(sql0)
    data = cursor.fetchone()
    if not data[0]:
        newfVID = 1
    else:
        newfVID = int(data[0]) 
    logger.debug('base file version id found is ' + str(data[0]))
    global base_fv_id 
    base_fv_id = newfVID        


    for f in mylist:
        base_fv_id+=1 
        logger.info( 'using ' + f)
        file_name = os.path.basename(f)
        logger.debug('file_name is ' + file_name)
        uuid = file_name[0:36]
        #aipUUID = aip[5:41]
        try:
            container1 = file_name[44:47]
            container2 = file_name[48:53]
        except:
            logger.error('file name does not have container ids in it')
            exit(5)
        
        #determine restrictions
        if restrictions == 'no':
            restrictions_apply = "False"
        elif restrictions == 'yes':
            restrictions_apply = "True"
            ead_actuate = "none"
            ead_show = "none"
        elif restrictions == 'premis':
            #get act and restrictions from Premis for this file
            #act == disseminate, restriction == Allow, then False
            #anything else True
            print "need premis for restrictions"
            act = mymets[uuid]['premis']['act']
            restriction = mymets[uuid]['premis']['restriction']
            if act == 'Disseminate' and restriction == 'Allow':
                restrictions_apply = False
            else:
                restrictions_apply = True
                ead_actuate = "none"
                ead_show = "none"
            
            
        #determine access_conditions
        if len(access_conditions) == 0 or restrictions == 'premis':
            #get rightsGranted note
            print "need premis for access conditions"
            rightsGrantedNote = mymets[uuid]['premis']['rightsGrantedNote']
            if rightsGrantedNote:
                access_conditions = rightsGrantedNote
            
            
        short_file_name = file_name[37:]
        time_now = strftime("%Y-%m-%d %H:%M:%S", localtime())
        file_uri = uri_prefix  + file_name
        sql1="select  d.archdescriptioninstancesid, c.resourceComponentId, c.dateBegin, c.dateEnd, c.dateExpression, c.title from resourcescomponents a join resourcescomponents b on (a.resourcecomponentid = b.parentresourcecomponentid) join resourcescomponents c on (b.resourcecomponentid = c.parentresourcecomponentid) join archdescriptioninstances d on (c.resourcecomponentid = d.resourcecomponentid) where a.resourceid = 31 and d.container1numericindicator = '%s' and d.container2numericindicator = '%s'" % ( container1, container2);
#sql1 = "select a.archDescriptionInstancesId, a.resourceComponentId, b.dateBegin, b.dateEnd, b.dateExpression from ArchDescriptionInstances a join ResourcesComponents b on a.resourceComponentId = b.resourceComponentId where (container1numericIndicator = '%s' and container2NumericIndicator = '%s')" % ( container1, container2)
        logger.info('sql1:' + sql1) 
        cursor.execute(sql1)
        #logger.info("ran sql1")
        data = cursor.fetchone()
        #logger.info("got one from sql1: " + str(len(data))) 
        archDID = data[0]
        rcid = data[1]
        dateBegin = data[2]
        dateEnd = data[3]
        dateExpression = data[4]
        rc_title = data[5]
        logger.info("found rc_title " + rc_title + ":" + str(len(rc_title)) ) 
        if (not rc_title or len(rc_title) == 0):
            if (not dateExpression or len(dateExpression) == 0):
                if dateBegin == dateEnd:
                    short_file_name = str(dateBegin)
                else:
                    short_file_name = str(dateBegin) + '-' + str(dateEnd)
            else:
                short_file_name = dateExpression
        else:
            short_file_name = rc_title

        logger.info("dateExpression is : " + str(dateExpression) + str(len(dateExpression)))
        logger.info("dates are  " + str(dateBegin) + "-" + str(dateEnd))
        logger.info("short file name is " + str(short_file_name))
 
        logger.info( "found archDescriptionInstancesId " + str(archDID) + ", rcid " + str(rcid))

        sql2 = "select repositoryId from Repositories" 
        logger.info('sql2: ' + sql2)

        cursor.execute(sql2)
        data = cursor.fetchone()
        repoId = data[0]
        logger.info('repoId: ' + str(repoId))
        sql3 = " select max(archDescriptionInstancesId) from ArchDescriptionInstances"
        logger.info('sql3: ' + sql3) 
        cursor.execute(sql3)
        data = cursor.fetchone()
        newaDID = int(data[0]) + 1

 
        sql4 = "insert into ArchDescriptionInstances (archDescriptionInstancesId, instanceDescriminator, instanceType, resourceComponentId) values (%d, 'digital','Digital object',%d)" % (newaDID, rcid)
        logger.debug('sql4:' + sql4)
        adid = process_sql(sql4)

        sql5 = """INSERT INTO DigitalObjects                  
           (`version`,`lastUpdated`,`created`,`lastUpdatedBy`,`createdBy`,`title`,
            `dateExpression`,`dateBegin`,`dateEnd`,`languageCode`,`restrictionsApply`,
            `eadDaoActuate`,`eadDaoShow`,`metsIdentifier`,`objectType`,`objectOrder`,
            `archDescriptionInstancesId`,`repositoryId`)
           VALUES (1,'%s', '%s','%s','%s','%s','%s',%d, %d,'English',%d,'%s','%s','%s','%s',0,%d,%d)""" % (time_now, time_now, atuser, atuser, short_file_name,dateExpression, dateBegin, dateEnd, restrictions_apply, ead_actuate, ead_show,uuid, object_type, newaDID, repoId)
        logger.info('sql5: ' + sql5)
        doID = process_sql(sql5)
        sql6 = """insert into FileVersions (fileVersionId, version, lastUpdated, created, lastUpdatedBy, createdBy, uri, useStatement, sequenceNumber, eadDaoActuate,eadDaoShow, digitalObjectId)
              values 
           (%d, 1, '%s', '%s', '%s', '%s', '%s', '%s', %d, '%s','%s', %d)""" % (base_fv_id,time_now, time_now,atuser,atuser,file_uri,use_statement,0, ead_actuate,ead_show, doID)
        logger.info('sql6: ' + sql6)
        process_sql(sql6)

        #create notes
        sql7 = " select max(archdescriptionrepeatingdataId) from archdescriptionrepeatingdata"
        logger.info('sql7: ' + sql7) 
        cursor.execute(sql7)
        data = cursor.fetchone()
       
        #existence and location of originals note 
        newadrd = int(data[0]) + 1
        seq_num = 0
        note_content = dip_uuid
        logger.info("about to run sql8")
        sql8 = """insert into archdescriptionrepeatingdata 
            (archdescriptionrepeatingdataid, descriminator, version, lastupdated, created, lastupdatedby ,createdby, repeatingdatatype, title, sequenceNumber,
            digitalObjectId, noteContent, notesetctypeid, basic, multiPart,internalOnly) values 
            (%d, 'note',%d, '%s', '%s', '%s', '%s','Note','', 0, %d, '%s',13, '', '', '')""" % (newadrd, seq_num, time_now, time_now, atuser, atuser, doID, note_content ) 
        logger.info('sql8: ' + sql8)
        adrd = process_sql(sql8) 
        
        #conditions governing access note
        newadrd += 1
        seq_num += 1
        note_content = access_conditions
        
        sql9 = """insert into archdescriptionrepeatingdata 
            (archdescriptionrepeatingdataid, descriminator, version, lastupdated, created, lastupdatedby ,createdby, repeatingdatatype, title, sequenceNumber,
            digitalObjectId, noteContent, notesetctypeid, basic, multipart, internalOnly) values 
            (%d, 'note',0, '%s', '%s', '%s', '%s','Note','', %d, %d, '%s',8, '', '', '')""" % (newadrd, time_now, time_now, atuser, atuser, seq_num, doID, note_content )
        adrd = process_sql(sql9) 
         
    
    process_sql("commit")

if __name__ == '__main__':
    
    RESTRICTIONS_CHOICES=[ 'yes', 'no', 'premis' ]
    EAD_SHOW_CHOICES=['embed', 'new', 'none', 'other', 'replace']
    EAD_ACTUATE_CHOICES=['none','onLoad','other', 'onRequest']

    parser = argparse.ArgumentParser(description="A program to take digital objects from a DIP and upload them to an archivists toolkit db")
    parser.add_argument('--host', default="localhost", dest="atdbhost", 
        metavar="host", help="hostname or ip of archivists toolkit db")
    parser.add_argument('--port', type=int, default=3306, dest='atdbport', 
        metavar="port", help="port used by archivists toolkit mysql db")
    parser.add_argument('--dbname', dest='atdb', metavar="db",
        help="name of mysql database used by archivists toolkit")
    parser.add_argument('--dbuser', dest='atdbuser', metavar="db user")
    parser.add_argument('--dbpass', dest='atdbpass', metavar="db password")
    parser.add_argument('--dip_location', metavar="dip location")
    parser.add_argument('--dip_name', metavar="dip name")
    parser.add_argument('--dip_uuid', metavar="dip uuid")
    parser.add_argument('--atuser', metavar="at user")
    parser.add_argument('--restrictions', metavar="restrictions apply", default="premis", choices=RESTRICTIONS_CHOICES)
    parser.add_argument('--object_type', metavar="object type", default="")
    parser.add_argument('--ead_actuate', metavar="ead actuate", default="onRequest", choices=EAD_ACTUATE_CHOICES) 
    parser.add_argument('--ead_show', metavar="ead show", default="new", choices=EAD_SHOW_CHOICES )
    parser.add_argument('--use_statement', metavar="use statement")
    parser.add_argument('--uri_prefix', metavar="uri prefix")
    parser.add_argument('--access_conditions', metavar="conditions governing access", default="")
    parser.add_argument('--use_conditions', metavar="conditions governing use", default="")
    parser.add_argument('--version', action='version', version='%(prog)s 0.1.0')
    args =  parser.parse_args()
    if not (args.atdb):
        get_user_input()
    
    try:
        mylist = get_files_from_dip(args.dip_location, args.dip_name, args.dip_uuid)
        upload_to_atk(mylist, args.atuser, args.ead_actuate, args.ead_show, args.object_type, args.use_statement, args.uri_prefix, args.dip_uuid, args.access_conditions, args.use_conditions, args.restrictions, args.dip_location)
        
    except Exception as exc:
        print exc
        exit(1) 

