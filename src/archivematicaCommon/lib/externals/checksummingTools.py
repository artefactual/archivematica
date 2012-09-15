#!/usr/bin/python -OO
import hashlib

#Borrowed from http://stackoverflow.com/questions/1131220/get-md5-hash-of-a-files-without-open-it-in-python
def md5_for_file(fileName, block_size=2**20):
    f = open(fileName)
    md5 = hashlib.md5()
    while True:
        data = f.read(block_size)
        if not data:
            break
        md5.update(data)
    #return md5.digest()
    return md5.hexdigest()

#Modification of above borrowed function
def sha_for_file(fileName, block_size=2**20):
    f = open(fileName)
    sha = hashlib.sha256()
    while True:
        data = f.read(block_size)
        if not data:
            break
        sha.update(data)
    #return sha.digest()
    return sha.hexdigest()


if __name__ == '__main__':
    import sys
    theFile = sys.argv[1]
    print "md5:", md5_for_file(theFile)
    print "sha256:", sha_for_file(theFile)
