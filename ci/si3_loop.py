# SI3-LOOP-01 v1.4 [beat45: 株十二多轨面+毂巷自扫+大堂@线名监测+线级日闸持久化] — 毂侧常驻事件驱动闭环引擎
# 谱系: qlv SI3-ENGINE-01 毂侧移植(修41谱) → v1.3 自铸 → v1.4 面桥(CASCADE-DRIVE-01/LANE-PATROL-01落器)
# 环: 未解项→路由→实证面直投(多轨)→幂等日推→闭环迁出; 毂巷双面自扫; 大堂@线名监测入plan
# 刀律: 线级新语义拍≤2/日(修43释律,持久化ext_day防多跑超发); 回执/邮政类不计; 司法自缚: dry默认,--live方推
import json, sys, os, base64, urllib.request, urllib.parse, datetime
GH='https://api.github.com'
def _mint():
    try:
        import jwt as JW, time as _t
        _k=open('/mnt/agents/output/.scratch/ciops_hub.pem').read()
        _n=int(_t.time())
        _j=JW.encode({'iat':_n-90,'exp':_n+540,'iss':'4621702'},_k,algorithm='RS256')
        _q=urllib.request.Request(GH+'/app/installations/154355791/access_tokens',method='POST',headers={'Authorization':'Bearer '+_j,'Accept':'application/vnd.github+json'})
        return json.loads(urllib.request.urlopen(_q,timeout=25).read())['token']
    except Exception: return None
TOK=_mint() or os.environ.get('LINE_PAT') or os.environ.get('GITHUB_TOKEN')
def H(t): return {'Authorization':'Bearer '+t,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}
def gh(t,p):
    q=urllib.request.Request(GH+p,headers=H(t))
    try:
        with urllib.request.urlopen(q,timeout=30) as r: return json.loads(r.read())
    except Exception as e: return {'__err':str(e)}
def gfile(t,repo,path):
    d=gh(t,'/repos/chepin-ai/%s/contents/%s'%(repo,urllib.parse.quote(path)))
    if isinstance(d,dict) and 'content' in d: return base64.b64decode(d['content']).decode(), d['sha']
    return None,None
def put(t,repo,path,text,msg,sha=None):
    body={'message':msg,'content':base64.b64encode(text.encode()).decode()}
    if sha: body['sha']=sha
    q=urllib.request.Request(GH+'/repos/chepin-ai/%s/contents/%s'%(repo,urllib.parse.quote(path)),
        data=json.dumps(body).encode(),headers=H(t),method='PUT')
    with urllib.request.urlopen(q,timeout=30) as r: return json.loads(r.read())

# 修45[株十二]: 线→实证面有序表(首=实证活面,次=备面; CASCADE-DRIVE-01 §四面图)
SURFACES={
 'usrm':[('vci-usrm','inbox')],
 'ucif2':[('ci-inbox','公告板'),('vci-ucif2','inbox')],
 'vinf':[('ci-inbox','lanes/vinf/inbox'),('vci-vinf','inbox')],
 'qlv':[('ci-inbox','lanes/qlv/inbox'),('vci-inbox','lanes/qlv/inbox')],
 'qtlv':[('ci-inbox','lanes/qtlv/inbox'),('vci-inbox','lanes/qtlv/inbox')],
 'qfa':[('vci-inbox','lanes/qfa/inbox'),('vci-qgl','inbox')],
 'lgt':[('vci-inbox','lanes/lgt/inbox')],
 'cfts':[('vci-cfts','inbox'),('vci-inbox','lanes/cfts/inbox')],
 'qgl':[('vci-qgl','inbox')]}
HUBLANES=[('ci-inbox','lanes/cisvr/inbox'),('vci-inbox','lanes/cisvr/inbox')]  # 修45[毂自盲]: 毂巷双面自扫
LINES=list(SURFACES)
DAY=datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%d')
TS=datetime.datetime.now(datetime.UTC).isoformat().replace('+00:00','Z')
LIVE='--live' in sys.argv
CAP_EXT=2; LINE_CAP=2; PUSH_MAX=6  # 修47[v1.5]: qfa-90日预算钱卫(总推日额)

def route(e):
    own=str(e.get('owner') or ''); st=str(e.get('state') or '')
    if 'root' in own or 'blocked' in st or 'presented' in st: return ('escalate',None)
    for ln in LINES:
        if ln in own: return ('answer-beat',ln)
    if any(k in own for k in ('all-lines','八线','全院','六线','全院(席次在帖)')): return ('cosign-invite',None)
    if 'cisvr' in own or '毂' in own: return ('self-advance',None)
    return ('review',None)

def hub_intake():
    out=[]
    for rp,pa in HUBLANES:
        d=gh(TOK,'/repos/chepin-ai/%s/contents/%s'%(rp,urllib.parse.quote(pa)))
        if isinstance(d,list):
            for f in d:
                if f['name']!='.gitkeep' and not f['name'].startswith('hub-'):
                    out.append('%s/%s/%s'%(rp,pa,f['name']))
    return out
def lobby_mentions():
    d=gh(TOK,'/repos/chepin-ai/vci-inbox/issues/1')
    nc=d.get('comments',0) if isinstance(d,dict) else 0
    if not nc: return []
    import math
    cs=gh(TOK,'/repos/chepin-ai/vci-inbox/issues/1/comments?per_page=100&page=%d'%math.ceil(nc/100))
    hits=[]
    if isinstance(cs,list):
        for c in cs[-20:]:
            b=c.get('body','')[:200]
            for ln in LINES:
                if ('@'+ln) in b and 'cisvr' not in b[:20]:
                    hits.append({'cid':c['id'],'line':ln,'ts':c['created_at'],'head':b[:60]}); break
    return hits

def main():
    reg_raw,_=gfile(TOK,'ci-control','bridge/disc/OPEN-REGISTER-01.json')
    if not reg_raw: print('[si3] register fetch fail — abort'); return
    reg=json.loads(reg_raw)
    opens=[e for e in reg.get('open',[]) if 'CLOSE' not in str(e.get('state','')).upper()]
    st_raw,st_sha=gfile(TOK,'ci-worker-01','receipts/tower/si3-state.json')
    st=json.loads(st_raw) if st_raw else {}
    ed=st.setdefault('ext_day',{})
    if ed.get('day')!=DAY: ed={'day':DAY,'n':0}; st['ext_day']=ed
    lb=st.setdefault('line_beats',{})
    plan=[]; pushed=[]; seeded=[]
    seen=st.setdefault('seen',{})
    bud=st.setdefault('budget',{})
    if bud.get('day')!=DAY: bud={'day':DAY,'total':0}; st['budget']=bud
    for e in opens:
        iid=str(e.get('id')); rt,ln=route(e)
        done_today = st.get('beats',{}).get(iid)==DAY
        plan.append({'id':iid,'route':rt,'line':ln,'pushed_today':done_today})
        first_sight = iid not in seen
        if first_sight: seen[iid]=DAY
        since_day=str(e.get('since') or DAY)[:10]
        seeded_skip = first_sight and since_day<DAY   # 修47[v1.5]boot律: 器装前之件首见只种不推(qfa-90互拍③)
        if seeded_skip: seeded.append(iid)
        if LIVE and not done_today and not seeded_skip and rt=='answer-beat' and ed['n']<CAP_EXT and bud['total']<PUSH_MAX and lb.get(ln,{}).get(DAY,0)<LINE_CAP:
            rp,pa=SURFACES[ln][0]
            ask=e.get('ask') or e.get('title') or iid
            sla='次拍' if ln in ('cfts','qgl') else '次醒拍'
            cap=('CLASSIFY: L1(联邦机器邮·毂SI3应答拍·免迁24h)\n【SI3-LOOP-01 · 应答拍 %s】%s\n题面: 上项在毂册未解, 请陈状态/阻点/所需。\n判据: 答件署线名+项号入本面(尔正典感面)。\n死线: %s(SLA分级)。\n——毂·SI3环v1.4(实证面直投, 幂等日推, 闭环即迁出)'%(iid,str(ask)[:120],sla))
            try:
                put(TOK,rp,'%s/SI3-%s-%s.md'%(pa,iid,DAY),cap,'SI3-LOOP-01 应答拍: %s @%s'%(iid,ln))
                st.setdefault('beats',{})[iid]=DAY; ed['n']+=1; bud['total']+=1
                lb.setdefault(ln,{})[DAY]=lb.get(ln,{}).get(DAY,0)+1
                pushed.append(iid)
            except Exception as ex:
                print('[si3] push fail',iid,str(ex)[:80])
    closed=[str(e.get('id')) for e in reg.get('open',[]) if 'CLOSE' in str(e.get('state','')).upper()]
    for cid in closed: st.get('beats',{}).pop(cid,None)
    hi=hub_intake(); lm=lobby_mentions()
    st['ts']=TS; st['open_count']=len(opens)
    rec={'v':'SI3-LOOP-01 v1.5','ts':TS,'live':LIVE,'open':len(opens),'plan':plan,'pushed':pushed,'seeded':seeded,'budget_today':bud['total'],
         'ext_today':ed['n'],'cap':CAP_EXT,'line_cap':LINE_CAP,
         'hub_intake_pending':hi,'lobby_mentions':lm[-8:],
         'law':'株十二实证面直投; 毂巷双面自扫; 大堂@线名监测; 线级日闸持久化; 幂等=item+day; 闭环迁出; 修47v1.5=boot律首见只种+CAS三段式落账+日预算钱卫PUSH_MAX=6(qfa-90互拍三件实装)'}
    print(json.dumps(rec,ensure_ascii=False,indent=1)[:2600])
    if LIVE:
        body=json.dumps(st,ensure_ascii=False,indent=1); sha=st_sha; cas_tries=0
        for _try in range(3):  # 修47[v1.5]CAS落账三段式+抢账恢复(qfa-90互拍②/FIX-05b,FIX-08基因)
            try:
                put(TOK,'ci-worker-01','receipts/tower/si3-state.json',body,'SI3-LOOP-01 v1.5 state %s'%TS, sha=sha); cas_tries=_try+1; break
            except Exception as ex:
                if '409' not in str(ex): raise
                r2,s2=gfile(TOK,'ci-worker-01','receipts/tower/si3-state.json')
                old=json.loads(r2) if r2 else {}
                for k in ('beats','seen'):
                    mg=old.get(k,{})
                    for a2,b2 in st.get(k,{}).items():
                        if str(b2)>=str(mg.get(a2,'')): mg[a2]=b2
                    st[k]=mg
                if old.get('ext_day',{}).get('day')==DAY:
                    st['ext_day']['n']=max(old['ext_day'].get('n',0),st['ext_day'].get('n',0))
                if old.get('budget',{}).get('day')==DAY:
                    st['budget']['total']=max(old['budget'].get('total',0),st['budget'].get('total',0))
                for ln2,dd2 in old.get('line_beats',{}).items():
                    for dd3,vv3 in dd2.items():
                        cur=st['line_beats'].setdefault(ln2,{}).get(dd3,0)
                        st['line_beats'][ln2][dd3]=max(vv3,cur)
                sha=s2; body=json.dumps(st,ensure_ascii=False,indent=1)
        rec['cas_tries']=cas_tries
        put(TOK,'ci-worker-01','receipts/tower/SI3-%s.json'%TS.replace(':','').replace('-',''),json.dumps(rec,ensure_ascii=False,indent=1),'SI3-LOOP-01 v1.5 receipt %s'%TS)
if __name__=='__main__': main()
