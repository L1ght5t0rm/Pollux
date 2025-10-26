#!/usr/bin/env python3

from json import loads,dumps
dumper=dumps
loader=loads
from base64 import b64decode,b64encode
def encoder(string): return b64encode(string).replace(b'=',b'.').replace(b'+',b'-').replace(b'/',b'_')[::-1]
def decoder(string): return b64decode( string[::-1].replace(b'.',b'=').replace(b'-',b'+').replace(b'_',b'/') )
matchMark=b'lS6c2aT'



from time import time
import re
pattern=re.escape(matchMark)+rb'(.*?)'+re.escape(matchMark[::-1])
from flask import Flask,request,render_template_string
cpp=Flask(__name__)



def getMsg(pollingInterval,init_timeout,init_cmds,**kwargs):
    updateMark=str(int( time()*1000 ))[::-1]
    pollingInterval=float( pollingInterval )
    init_timeout=float( init_timeout )
    init_cmds=init_cmds.splitlines()
    data={
        'updateMark': updateMark,
        'pollingInterval': pollingInterval,
        'init': {'timeout': init_timeout,'cmd':init_cmds}
        }
    for key,value in kwargs.items():
        if value:
            data[key]=value
    data=matchMark+encoder( dumper(data).encode() )+matchMark[::-1]
    return data
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




HTML_TEMPLATE='''
<!DOCTYPE html>
<html>
<head>
    <title>generater</title>
    <style>
        body {
            margin: 20px;
            max-width: 80%;
            margin-left: auto;
            margin-right: auto;
        }
        pre {
            white-space: pre-wrap;
            word-wrap: break-word;
            max-width: 100%;
            overflow-x: auto;
            background: #f5f5f5;
            padding: 10px;
            border-radius: 5px;
        }
        textarea {
            width: 100%;
            box-sizing: border-box;
            height: 150px;
        }
        .nav {
            margin-bottom: 20px;
        }
        .nav a {
            margin-right: 20px;
            text-decoration: none;
            font-size: 18px;
        }
        .nav a.active {
            font-weight: bold;
            color: #007cba;
        }
    </style>
</head>
<body>
    <h1>Generate/Decode tool</h1>


    {% if page=='encode' %}
    <div class="nav"><a href="/decode" target="_blank">Decode</a></div>
    <div>
        <h2>Generate</h2>
        <form method="post" action="/encode">
            <label>轮询间隔</label>
            <input type="number" name="pollingInterval" value="{{ pollingInterval or '10.0' }}" step="any" style="width: 30%; margin-bottom: 10px;">
            <br><label>init命令组超时</label>
            <input type="number" name="init_timeout" value="{{ init_timeout or '10.0' }}" step="any" style="width: 30%; margin-bottom: 10px;">
            <br><label>init命令组</label>
            <textarea name="init_cmds" rows="8">{{ init_cmds or 'whoami\nid\necho 1\nsysteminfo\ncat /etc/os-release' }}</textarea>
            <br><label>extra json</label>
            <textarea name="extra_json" rows="3" placeholder="{\n'task1':{'timeout':10.0,'cmd':['whoami','id']},\n'task2':{'timeout':5.0,'cmd':['pwd']}\n}">{{ extra_json or '' }}</textarea>
            <br><button type="submit">Generate</button>
        </form>
    </div>
    {% endif %}

    {% if page=='decode' %}
    <div>
        <h2>Decode</h2>
        <form method="post" action="/decode">
            <textarea name="decode_data" rows="8" placeholder="Input the data to be decoded...">{{ decode_data or '' }}</textarea><br>
            <button type="submit">Decode</button>
        </form>
    </div>
    {% endif %}

    {% if result %}
    <div style="margin-top: 30px;">
        <h2>result:</h2>
        <pre>{{ result }}</pre>
    </div>
    {% endif %}
</body>
</html>
'''



@cpp.route('/encode',methods=['GET','POST'])
def encode_page():
    if request.method=='POST':
        init_cmds=request.form.get('init_cmds')
        pollingInterval=request.form.get('pollingInterval')
        init_timeout=request.form.get('init_timeout')

        extra_json=request.form.get('extra_json')
        try:
            extra_data={}
            if extra_json.strip():
                extra_json=extra_json.replace("'",'"')
                extra_data=loads(extra_json)
                if not isinstance(extra_data,dict):
                    raise ValueError(f"extra_json must be dict type")
                '''
                for key,value in extra_data.items():
                    if not isinstance(value,dict):
                        raise ValueError(f"The command group '{key}' must be dict type.")
                    if 'timeout' not in value or 'cmd' not in value:
                        raise ValueError(f"The command group '{key}' must contain 'timeout' and 'cmd' keys")
                '''
            encoded_msg=getMsg(pollingInterval,init_timeout,init_cmds,**extra_data)
            with open('copy-cmd.txt','wb') as f:
                f.write(encoded_msg)
            result=f"Encoding successful:\n{encoded_msg.decode()}"
        except Exception as e:
            result=f"Encoding failed: {str(e)}"

        return render_template_string(HTML_TEMPLATE,
                                    page='encode',
                                    result=result,
                                    init_cmds=init_cmds,
                                    pollingInterval=pollingInterval,
                                    init_timeout=init_timeout,
                                    extra_json=extra_json)
    return render_template_string(HTML_TEMPLATE)


@cpp.route('/decode',methods=['GET','POST'])
def decode_page():
    if request.method=='POST':
        decode_data=request.form.get('decode_data','')
        try:
            decoded=deMsg(decode_data)
            result=f"Decoding successful:\n{dumps(decoded,indent=2,ensure_ascii=False)}"
        except Exception as e:
            result=f"Decoding failed: {str(e)}"

        return render_template_string(HTML_TEMPLATE,
                                    page='decode',
                                    result=result,
                                    decode_data=decode_data)
    return render_template_string(HTML_TEMPLATE,page='decode')

@cpp.route('/')
def index():
    return render_template_string(HTML_TEMPLATE,page='encode')




if __name__=='__main__':
    #cpp.run(host='127.0.0.1',port=5200,debug=True)
    cpp.run(host='0.0.0.0',port=5200)





