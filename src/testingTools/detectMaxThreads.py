#!/usr/bin/python -OO
#Kirby Angell
#http://bytes.com/topic/python/answers/36549-maximum-number-threads
#Jul 18 '05

import thread, time
import threading
testAsSubThread = True

def t2():
    time.sleep( 1000 )

def maxThreadCountTest():
    tc = 0
    try:
        while 1:
            t = threading.Thread(target=t2)
            t.daemon = True
            t.start()
            #newThread = thread.start_new_thread( t, () )
            tc += 1
            print "tc: ", threading.activeCount(), tc
            time.sleep( 0.05 )

    except Exception as inst:
        print type(inst)     # the exception instance
        print inst.args      # arguments stored in .args
        print inst           # __str__ allows args to printed directly
    finally:
        print "final", tc
        exit(tc)

if __name__ == '__main__':
    if testAsSubThread:
        newThread = thread.start_new_thread(maxThreadCountTest, ())
        while 1:
            time.sleep(1000)
    else:
        maxThreadCountTest()
