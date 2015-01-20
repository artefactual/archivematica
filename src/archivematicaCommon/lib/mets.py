
import xml.sax
import subprocess    
from collections import defaultdict
 

class Tree(defaultdict):
    def __init__(self, value=None):
        super(Tree, self).__init__(Tree)
        self.value = value
        

class MetsFile():
    
    """ 
    Representation of a mets xml file.
    
    Provides metadata and other details about a given mets file.
    """
    
    def __init__(self, sourceFileName):
        #source = open(sourceFileName)
        self.file_name = sourceFileName
        self.lines = self.file_len()
        
    def parse(self):
        """Open and read the entire mets file.  Populate a nested defaultdict with results."""
        source = open(self.file_name)
        dh = MetsContentHandler()
        parser = xml.sax.make_parser()
        parser.setContentHandler(dh)
        parser.parse(source)
        
        self.mets = dh.mets
        
    def file_len(self):
        with open(self.file_name) as f:
            for i, l in enumerate(f):
                pass
        return i + 1
    
    # this version of file_len might work better on larger files, not tested yet
    #def file_len(self):
    #    p = subprocess.Popen(['wc', '-l', self.fileName], stdout=subprocess.PIPE, 
    #                                                      stderr=subprocess.PIPE)
    #    result, err = p.communicate()
    #    if p.returncode != 0:
    #        raise IOError(err)
    #    return int(result.strip().split()[0])
    
    
    
class MetsContentHandler(xml.sax.ContentHandler):
    def __init__(self):
        xml.sax.ContentHandler.__init__(self)
        self.data = ""
        
        # this is a dictionary that will have one entry for each file listed in this mets file
        self.mets = Tree()
        
        self.file_uuid = None
        self.act_text = None
        self.rightsGrantedNote_text = None
        self.restriction_text = None
        
        #METS files have a few different top level tags these flags show
        #which section we are currently in when parsing
        
        self.in_metsHdr = 0
        self.in_amdSec = 0
        self.in_fileSec = 0
                
        #inside amdSec, there are optional subsections:
        self.in_techMD = 0
        self.in_rightsMD = 0
        self.in_rightsGranted = 0
        self.in_objectCharacteristics = 0
        
        
    def startElement(self, name, attrs):
        if name == "metsHdr":
            self.in_metsHdr = 1
            
        if name == "amdSec":
            self.in_amdSec = 1
            #print "entering: " + attrs.get('ID')
        if name == "fileSec":
            self.in_fileSec = 1
        if name == "techMD":
            self.in_techMD = 1
            #print "\t: " + attrs.get('ID')
        if name == "rightsMD":
            self.in_rightsMD = 1
            #print "\t: " + attrs.get('ID')     
        if name == "objectCharacteristics":
            self.in_objectCharacteristics = 1     
        if name == "rightsGranted":
            self.in_rightsGranted = 1
    
    def endElement(self, name):
        if name == "metsHdr":
            self.in_metsHdr = 0
        if name == "amdSec":
            self.in_amdSec = 0
        if name == "fileSec":
            self.in_fileSec = 0
        if name == "techMD":
            self.in_techMD = 0
            #print "leaving techMD"
        if name == "rightsMD":
            self.in_rightsMD = 0 
            self.size = ""
            self.file_uuid = ""
        if name == "rightsGranted":
            self.in_rightsGranted = 0
            
        if name == "objectCharacteristics":
            self.in_objectCharacteristics = 0     
        if name == "objectIdentifierValue":
            self.file_uuid = self.data.strip()
            #print "leaving object identifier value \t: "  + self.file_uuid 
        if name == "size":
            if self.in_techMD and self.in_objectCharacteristics:
               self.mets[self.file_uuid]['size'] =  self.data.strip()
        #if name == "objectIdentifier":
            #print "leaving objectIdentifier"
        if name  == "act":
            if self.in_rightsMD:
                 self.mets [self.file_uuid]['premis']['act'] = self.data.strip()
        
        if name == "rightsGrantedNote":
            if self.in_rightsMD:
                self.mets [self.file_uuid]['premis']['rightsGrantedNote'] = self.data.strip()
                #print "leaving rightsGrantedNote"
        
        if name == "restriction":
            if self.in_rightsMD:
                self.mets [self.file_uuid]['premis']['restriction'] = self.data.strip()
                #print "leaving restriction"
                  
        self.data = ""

    #occurs as each character is processed into the parser. data is a running tally of info within element.
    def characters(self, data):
        self.data += data
        
def main(sourceFileName):
    print "working on " + sourceFileName
    
    mymets = MetsFile(sourceFileName)
    
    print 'lines in file: ' + str(mymets.lines)
    mymets.parse()
    
    mets = mymets.mets
    for uuid in mets.keys():
            print uuid
            print mets[uuid]['size']
            if mets[uuid]['premis']:
                print mets[uuid]['premis']['restriction']
                print mets[uuid]['premis']['rightsGrantedNote']
            else:
                print "no premis"
    
   
if __name__ == "__main__":
    file_name='METS.2e0bde80-3c98-4934-b668-3f62818525c1.xml'
    main(file_name)

