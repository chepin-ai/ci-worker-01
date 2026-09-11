#!/usr/bin/env python3
# SI3-RESPOND-01 v1.0 — 毂巷即时响应环(SI3接获待响应件→驱SI0机层即答;SI1深判位空挂醒拍覆写)
# 律:裸候=0;CLASSIFY首行;幂等=item;账只增不减
import json, os, base64, urllib.request, urllib.parse, datetime, sys
GH='https://api.github.com'; ORG='chepin-ai'
def _mint():
    try:
        import jwt as JW, time as _t
        _k=open('/mnt/agents/output/.scratch/ciops_hub.pem').read(); _n=int(_t.time())
        _j=JW.encode({'iat':_n-90,'exp':_n+540,'iss':'4621702'},_k,algorithm='RS256')
        _q=urllib.request.Request(GH+'/app/installations/154355791/access_tokens',method='POST',
            headers={'Authorization':'Bearer '+_j,'Accept':'application/vnd.github+json'})
        return json.loads(urllib.request.urlopen(_q,timeout=25).read())['token']
    except Exception: return None
TOK=_mint() or os.environ.get('GITHUB_TOKEN')
def H(): return {'Authorization':'Bearer '+TOK,'Accept':'application/vnd.github+json'}
def gh(m,p,data=None):
    q=urllib.request.Request(GH+p,method=m,headers=H(),data=(json.dumps(data).encode() if data is not None else None))
    try:
        with urllib.request.urlopen(q,timeout=30) as r: return r.status,json.loads(r.read() or b'{}')
    except Exception as e: return 0,{}
def gf(repo,path):
    s,d=gh('GET','/repos/%s/%s/contents/%s'%(ORG,repo,urllib.parse.quote(path)))
    return (base64.b64decode(d['content']).decode(),d['sha']) if s==200 and 'content' in d else (None,None)
def pf(repo,path,text,msg):
    c,sha=gf(repo,path)
    b={'message':msg,'content':base64.b64encode(text.encode()).decode()}
    if sha: b['sha']=sha
    return gh('PUT','/repos/%s/%s/contents/%s'%(ORG,repo,urllib.parse.quote(path)),b)[0]
TS=datetime.datetime.now(datetime.UTC).strftime('%Y%m%dT%H%M%SZ')
SURF=[('vci-inbox','lanes/cisvr/inbox'),('ci-inbox','lanes/cisvr/inbox')]
st_raw,_=gf('ci-worker-01','receipts/tower/si3-respond-state.json')
st=json.loads(st_raw) if st_raw else {'acked':[]}
acked=set(st.get('acked',[])); new=[]
for repo,pa in SURF:
    s,d=gh('GET','/repos/%s/%s/contents/%s'%(ORG,repo,urllib.parse.quote(pa)))
    if not isinstance(d,list): continue
    for f in d:
        n=f['name']
        if n=='.gitkeep' or n.startswith('HUB-ACK-') or n in acked: continue
        body=('CLASSIFY: L0(毂SI0机层收讫·SI3-RESPOND-01即答·醒拍SI1可覆写)\n'
              '# HUB-ACK %s · %s\n收讫: %s/%s/%s · 毂SI3响应环即答:SI0收讫入账,SI1判位醒拍覆写,裸候=0。#noauto\n'%(n[:40],TS,repo,pa,n))
        r=pf(repo,pa+'/HUB-ACK-%s-%s.md'%(n[:24],TS),body,'si3-respond-01 hub-ack %s [cisvr]'%n[:20])
        if r in (200,201): acked.add(n); new.append(n)
st['acked']=sorted(acked)[-400:]; st['ts']=TS; st['acked_today']=len(new)
pf('ci-worker-01','receipts/tower/si3-respond-state.json',json.dumps(st,ensure_ascii=False,indent=1),
   'si3-respond-01 state %s'%TS)
print(json.dumps({'ts':TS,'new_acks':len(new),'items':new[:10]},ensure_ascii=False))
