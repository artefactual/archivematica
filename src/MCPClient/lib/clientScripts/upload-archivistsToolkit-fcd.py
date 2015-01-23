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
import sys, traceback
import MySQLdb
from time import localtime, strftime
import argparse
import logging
# archivematicaCommon
import archivistsToolkit.atk as atk
import mets
from xml2obj import mets_file
import databaseInterface

#global variables
db = None
cursor = None
testMode =0 
base_fv_id = 1

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
logger.addHandler(logging.FileHandler('/tmp/at_upload.log', mode='a'))


    
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

def get_pairs(dip_uuid):
    pairs = dict()
    #connect to archivematica db, make a set of pairs from pairs table
   
    sql = """SELECT fileUUID, resourceId, resourceComponentId from AtkDIPObjectResourcePairing where dipUUID = '{}'""".format(dip_uuid)
    c, sqlLock = databaseInterface.querySQL(sql)
    dbresult = c.fetchall()
    for item in dbresult:
        ids = dict()
        ids['rid'] = item[1]
        ids['rcid'] = item[2]
        pairs[item[0]] =  ids
    sqlLock.release()
    return pairs

def delete_pairs(dip_uuid):
    sql = """delete from AtkDIPObjectResourcePairing where dipUUID = '{}'""".format(dip_uuid)
    c, sqlLock = databaseInterface.querySQL(sql)
    sqlLock.release()
      
def upload_to_atk(mylist, atuser, ead_actuate, ead_show, object_type, use_statement, uri_prefix, dip_uuid, access_conditions, use_conditions, restrictions, dip_location):
    #TODO get resource_id from caller
    resource_id = 31
    if uri_prefix[-1] == '/':
        uri_prefix = uri_prefix + dip_uuid + "/objects/"
    else:
        uri_prefix = uri_prefix + "/" + dip_uuid + "/objects/"
        
    #get mets object if needed
    mets = None
    if restrictions == 'premis' or len(access_conditions) == 0 or len(use_conditions) == 0:
        try:
            logger.debug("looking for mets: {}".format(dip_uuid))
            mets_source = dip_location + 'METS.' + dip_uuid + '.xml'
            logger.debug ("mets is at " + mets_source) 
            mets = mets_file(mets_source)
            logger.debug("found mets file")
        except Exception:
            raise
            exit(4)
           
    global db
    global cursor
    db = atk.connect_db(args.atdbhost, args.atdbport, args.atdbuser, args.atdbpass, args.atdb)
    cursor = db.cursor()
    #get a list of all the items in this collection
    col = atk.collection_list(db, resource_id)
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

    #pairs = get_pairs(dip_uuid)
    #TODO test to make sure we got some pairs
    
    for f in mylist:
        base_fv_id+=1 
        logger.debug( 'using ' + f)
        file_name = os.path.basename(f)
        #logger.info('file_name is ' + file_name)
        uuid = file_name[0:36]
        #aipUUID = aip[5:41]
        access_restrictions = None
        access_rightsGrantedNote = None
        use_restrictions = None
        use_rightsGrantedNote = None
        #logging.info("looking for mets")
        if mets and mets[uuid]:
            #get premis info from mets
            for premis in mets[uuid]['premis']:
                logger.debug("{} rights = {}, note={}".format(premis, mets[uuid]['premis'][premis]['restriction'],mets[uuid]['premis'][premis]['rightsGrantedNote']))
                if premis == 'Disseminate':
                    access_restrictions = mets[uuid]['premis']['Disseminate']['restriction']
                    access_rightsGrantedNote = mets[uuid]['premis']['Disseminate']['rightsGrantedNote']
                if premis == 'Publish':
                    use_restrictions = mets[uuid]['premis']['Publish']['restriction']
                    use_rightsGrantedNote = mets[uuid]['premis']['Publish']['rightsGrantedNote']
        else:
            logger.debug("no mets or uuid")
        try:
            container1 = file_name[44:47]
            container2 = file_name[48:53]
        except:
            logger.error('file name does not have container ids in it')
            exit(5)
        #determine restrictions
        if restrictions == 'no':
            restrictions_apply = False
        elif restrictions == 'yes':
            restrictions_apply = True
            ead_actuate = "none"
            ead_show = "none"
        elif restrictions == 'premis':
            if access_restrictions == 'Allow' and use_restrictions == 'Allow':
                restrictions_apply = False
            else:
                restrictions_apply = True
                ead_actuate = "none"
                ead_show = "none"        
                
        if len(use_conditions) == 0 or restrictions == 'premis':
            if use_rightsGrantedNote:
                use_conditions = use_rightsGrantedNote

        if len(access_conditions) == 0 or restrictions == 'premis':
            if access_rightsGrantedNote:
                access_conditions = access_rightsGrantedNote
        
        short_file_name = file_name[37:]
        time_now = strftime("%Y-%m-%d %H:%M:%S", localtime())
        file_uri = uri_prefix  + file_name
        logger.debug("trying " + container1 + " " + container2)
        try:
            sql1="select  d.archdescriptioninstancesid, c.resourceComponentId, c.dateBegin, c.dateEnd, c.dateExpression, c.title from resourcescomponents a join resourcescomponents b on (a.resourcecomponentid = b.parentresourcecomponentid) join resourcescomponents c on (b.resourcecomponentid = c.parentresourcecomponentid) join archdescriptioninstances d on (c.resourcecomponentid = d.resourcecomponentid) where a.resourceid = 31 and d.container1numericindicator = '%s' and d.container2numericindicator = '%s'" % ( container1, container2)
      
            logger.debug('sql1:' + sql1) 
            cursor.execute(sql1)
            data = None
            if cursor.rowcount == 0:
                logger.debug("trying 2 levels of description instead")
                sql1b="""select  d.archdescriptioninstancesid, b.resourceComponentId, b.dateBegin, b.dateEnd, b.dateExpression, b.title 
                          from resourcescomponents a join resourcescomponents b on (a.resourcecomponentid = b.parentresourcecomponentid) 
                          join archdescriptioninstances d on (b.resourcecomponentid = d.resourcecomponentid) 
                          where a.resourceid = 31 and d.container1numericindicator = '%s' and d.container2numericindicator = '%s'""" % ( container1, container2) 
                cursor.execute(sql1b)
                if cursor.rowcount == 0:
                    logger.debug("trying 4 levels of description now last try")
                    sql1c="""select  d.archdescriptioninstancesid, c.resourceComponentId, c.dateBegin, c.dateEnd, c.dateExpression, c.title 
                             from resourcescomponents a join resourcescomponents f on (a.resourcecomponentid = f.parentresourcecomponentid) 
                             join resourcescomponents b on (f.resourcecomponentid = b.parentresourcecomponentid)  
                             join resourcescomponents c on (b.resourcecomponentid = c.parentresourcecomponentid) 
                             join archdescriptioninstances d on (c.resourcecomponentid = d.resourcecomponentid) 
                             where a.resourceid = 31 and d.container1numericindicator ='%s' 
                             and d.container2numericindicator = '%s'""" % ( container1, container2)
                    cursor.execute(sql1c)
                    if cursor.rowcount == 0:
                        logger.info("Missing ArchDescription: " + container1 + " " + container2)
                        continue 
            data = cursor.fetchone()
            logger.info("Found ArchDescription: " + container1 + " " + container2)    
        except:
            logger.info("problem")
            print '-'*60
            traceback.print_exc(file=sys.stdout)
            print '-'*60
            continue   
  
        oldadid = data[0] 
        rcid = data[1]
        dateBegin = data[2]
        dateEnd = data[3]
        dateExpression = data[4]
        rc_title = data[5]
        if (not rc_title or len(rc_title) == 0):
            if (not dateExpression or len(str(dateExpression)) == 0):
                if dateBegin == dateEnd:
                    short_file_name = str(dateBegin)
                else:
                    short_file_name = str(dateBegin) + '-' + str(dateEnd)
            else:
                short_file_name = dateExpression
        else:
            short_file_name = rc_title
        short_file_name = MySQLdb.escape_string(short_file_name) 
        sql2 = "select repositoryId from Repositories" 
        logger.debug('sql2: ' + sql2)

        cursor.execute(sql2)
        data = cursor.fetchone()
        repoId = data[0]
        logger.debug('repoId: ' + str(repoId))
        sql3 = " select max(archDescriptionInstancesId) from ArchDescriptionInstances"
        logger.debug('sql3: ' + sql3) 
        cursor.execute(sql3)
        data = cursor.fetchone()
        newaDID = int(data[0]) + 1

        sql4 = "insert into ArchDescriptionInstances (archDescriptionInstancesId, instanceDescriminator, instanceType, resourceComponentId) values (%d, 'digital','Digital object',%d)" % (newaDID, rcid)
        
        logger.debug('sql4:' + sql4)
        adid = process_sql(sql4)
        #added sanity checks in case date fields in original archival description were all empty
        if len(dateExpression) == 0:
            dateExpression = 'null'
        if not dateBegin: 
            dateBegin = 0
        if not dateEnd:
            dateEnd = 0
         
        sql5 = "INSERT INTO DigitalObjects (`version`,`lastUpdated`,`created`,`lastUpdatedBy`,`createdBy`,`title`,`dateExpression`,`dateBegin`,`dateEnd`,`languageCode`,`restrictionsApply`,`eadDaoActuate`,`eadDaoShow`,`metsIdentifier`,`objectType`,`objectOrder`,`archDescriptionInstancesId`,`repositoryId`) VALUES (1,'%s', '%s','%s','%s','%s','%s',%d, %d,'English',%d,'%s','%s','%s','%s',0,%d,%d)" % (time_now, time_now, atuser, atuser, short_file_name,dateExpression, dateBegin, dateEnd, int(restrictions_apply), ead_actuate, ead_show,uuid, object_type, newaDID, repoId)
        logger.debug('sql5: ' + sql5)
        doID = process_sql(sql5)
        sql6 = """insert into FileVersions (fileVersionId, version, lastUpdated, created, lastUpdatedBy, createdBy, uri, useStatement, sequenceNumber, eadDaoActuate,eadDaoShow, digitalObjectId)
              values 
           (%d, 1, '%s', '%s', '%s', '%s', '%s', '%s', %d, '%s','%s', %d)""" % (base_fv_id,time_now, time_now,atuser,atuser,file_uri,use_statement,0, ead_actuate,ead_show, doID)
        logger.debug('sql6: ' + sql6)
        process_sql(sql6)

        #create notes
        sql7 = " select max(archdescriptionrepeatingdataId) from archdescriptionrepeatingdata"
        logger.debug('sql7: ' + sql7) 
        cursor.execute(sql7)
        data = cursor.fetchone()
       
        #existence and location of originals note 
        newadrd = int(data[0]) + 1
        seq_num = 0
        note_content = dip_uuid
        logger.debug("about to run sql8")
        sql8 = """insert into archdescriptionrepeatingdata 
            (archdescriptionrepeatingdataid, descriminator, version, lastupdated, created, lastupdatedby ,createdby, repeatingdatatype, title, sequenceNumber,
            digitalObjectId, noteContent, notesetctypeid, basic, multiPart,internalOnly) values 
            (%d, 'note',%d, '%s', '%s', '%s', '%s','Note','', 0, %d, '%s',13, '', '', '')""" % (newadrd, seq_num, time_now, time_now, atuser, atuser, doID, note_content ) 
        logger.debug('sql8: ' + sql8)
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
        logger.debug('sql9:' + sql9)
         
        #conditions governing use` note
        newadrd += 1
        seq_num += 1
        note_content = use_conditions

        sql10 = """insert into archdescriptionrepeatingdata 
            (archdescriptionrepeatingdataid, descriminator, version, lastupdated, created, lastupdatedby ,createdby, repeatingdatatype, title, sequenceNumber,
            digitalObjectId, noteContent, notesetctypeid, basic, multipart, internalOnly) values 
            (%d, 'note',0, '%s', '%s', '%s', '%s','Note','', %d, %d, '%s',9, '', '', '')""" % (newadrd, time_now, time_now, atuser, atuser, seq_num, doID, note_content )
        adrd = process_sql(sql10)
        logger.debug('sql10:' + sql10)
   
    process_sql("commit")
    delete_pairs(dip_uuid)
    logger.info("completed upload successfully")
    
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

