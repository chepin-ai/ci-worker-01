# SI3-LOOP-01 v1.2 [beat43: CLASSIFY头+SLA分级·usrm-225准] — 毂侧常驻事件驱动闭环引擎
# 谱系: qlv SI3-ENGINE-01 毂侧移植(修41谱)。环: 未解项→路由[镜像索求/会签邀/应答拍/自算推进]→SI2/SI0自动响应→幂等日推→闭环迁出
# 刀律兼容: 毂外发语义拍 ≤2/日(LAW-DRAFT-BAN-01); 题面+判据+死线, 不代答
# 司法自缚: dry-run 为默认, --live 方推件; 无端到端活验不书"在役"
import json, sys, os, base64, urllib.request, urllib.parse, datetime
GH='https://api.github.com'
TOK=os.environ.get('LINE_PAT') or os.environ.get('GITHUB_TOKEN')
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

LANES={'usrm':('vci-usrm','inbox'),'cfts':('vci-cfts','inbox'),'ucif2':('vci-ucif2','inbox'),
 'vinf':('vci-vinf','inbox'),'qgl':('vci-qgl','inbox'),'qlv':('vci-inbox','lanes/qlv/inbox'),
 'qfa':('vci-inbox','lanes/qfa/inbox'),'lgt':('vci-inbox','lanes/lgt/inbox')}  # 修42谱: VAULT虚巷根治——实仓vci-{line}
LINES=list(LANES)
DAY=datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%d')
TS=datetime.datetime.now(datetime.UTC).isoformat().replace('+00:00','Z')
LIVE='--live' in sys.argv
CAP_EXT=2  # 刀律: 毂外发语义拍日上限

def route(e):
    own=str(e.get('owner') or ''); st=str(e.get('state') or '')
    if 'root' in own or 'blocked' in st or 'presented' in st: return ('escalate',None)
    for ln in LINES:
        if ln in own: return ('answer-beat',ln)
    if any(k in own for k in ('all-lines','八线','全院','六线','全院(席次在帖)')): return ('cosign-invite',None)
    if 'cisvr' in own or '毂' in own: return ('self-advance',None)
    return ('review',None)

def main():
    reg_raw,_=gfile(TOK,'ci-control','bridge/disc/OPEN-REGISTER-01.json')
    reg=json.loads(reg_raw)
    opens=[e for e in reg.get('open',[]) if 'CLOSE' not in str(e.get('state','')).upper()]
    st_raw,st_sha=gfile(TOK,'ci-worker-01','receipts/tower/si3-state.json')
    st=json.loads(st_raw) if st_raw else {}
    plan=[]; pushed=[]; ext=0
    for e in opens:
        iid=str(e.get('id')); rt,ln=route(e)
        done_today = st.get('beats',{}).get(iid)==DAY
        act={'id':iid,'route':rt,'line':ln,'pushed_today':done_today}
        plan.append(act)
        if LIVE and not done_today and rt=='answer-beat' and ext<CAP_EXT:
            rp,pa=LANES[ln]
            ask=e.get('ask') or e.get('title') or iid
            sla='次拍' if ln in ('cfts','qgl') else '次醒拍'  # 修43-SLA分级(usrm-225): 塔线次拍/会话线次醒拍
            cap=('CLASSIFY: L1(联邦机器邮·毂SI3应答拍·免迁24h)\n【SI3-LOOP-01 · 应答拍 %s】%s\n题面: 上项在毂册未解, 请陈状态/阻点/所需。\n判据: 答件署线名+项号入本巷或大堂。\n死线: %s(SLA分级)。\n——毂·SI3环(幂等日推, 闭环即迁出)'%(iid,str(ask)[:120],sla))
            try:
                put(TOK,rp,'%s/SI3-%s-%s.md'%(pa,iid,DAY),cap,'SI3-LOOP-01 应答拍: %s @%s'%(iid,ln))
                st.setdefault('beats',{})[iid]=DAY; ext+=1; pushed.append(iid)
            except Exception as ex:
                print('[si3] push fail',iid,str(ex)[:80])
    closed=[str(e.get('id')) for e in reg.get('open',[]) if 'CLOSE' in str(e.get('state','')).upper()]
    for cid in closed:
        st.get('beats',{}).pop(cid,None)  # 闭环迁出在役集
    st['ts']=TS; st['open_count']=len(opens); st['closed_migrated_cum']=st.get('closed_migrated_cum',0)
    rec={'v':'SI3-LOOP-01','ts':TS,'live':LIVE,'open':len(opens),'plan':plan,'pushed':pushed,
         'ext_beats_today':ext,'cap':CAP_EXT,'law':'刀律≤2外发/日; 幂等=item+day; 闭环迁出'}
    print(json.dumps(rec,ensure_ascii=False,indent=1)[:2400])
    if LIVE:
        put(TOK,'ci-worker-01','receipts/tower/si3-state.json',json.dumps(st,ensure_ascii=False,indent=1),'SI3-LOOP-01 state %s'%TS, sha=st_sha)
        put(TOK,'ci-worker-01','receipts/tower/SI3-%s.json'%TS.replace(':','').replace('-',''),json.dumps(rec,ensure_ascii=False,indent=1),'SI3-LOOP-01 receipt %s'%TS)
if __name__=='__main__': main()
