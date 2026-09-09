# hub_tower.py — HUB-TOWER-01 · 毂SI0镜像分身（TOWER-PARADIGM-01第四移植：qlv→qgl→[vinf候]→hub）
# 纯事件驱动：无定时器；外部唤起（push|issues|issue_comment|repository_dispatch|workflow_dispatch）
# 职：巡联邦面（板面三线像/@cisvr件/lane线声/毂inbox）→ 判词纪要落账 → 三线像现或急件→SPARK-HOOK毂inbox邮报（队列制，SI1注入合格制·修正案A2 2026-09-09(trivial永禁)）→ 债线驱动落OTP-SI2胶囊(修9 DRIVE-ENGINE-01,候线制废) → 对位催化落火种胶囊(修10 CATALYSIS-01,候「如何」之候废) → 有候件自唤下拍
# 三律防自激：拍内休眠冷却 / 空转计数骑payload链传连空熔断 / 无候件不出拍。SPARK-HOOK每拍至多一发，仅三线像现或毂inbox急件。
# 钥：env KIMI_API_KEY / LINE_PAT(CI_OPS_LINE_KEY) / GITHUB_TOKEN。值永不入文、永不打印。
import json, os, sys, time, hashlib, subprocess, urllib.request, urllib.error, urllib.parse

REPO = os.environ.get('GITHUB_REPOSITORY', 'chepin-ai/ci-worker-01')
GH = 'https://api.github.com'
SELFTEST = '--selftest' in sys.argv

def _env(name):
    v = os.environ.get(name, '').strip()
    return v if v else None

def ghget(token, path):
    req = urllib.request.Request(GH+path, headers={'Authorization':'token '+token,'Accept':'application/vnd.github+json','User-Agent':'hub-tower'})
    for i in range(4):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=25).read().decode() or '{}')
        except urllib.error.HTTPError as e:
            print(f'[ghget] HTTP {e.code} {path[:70]} try{i}')
            if i == 3: return {}
            time.sleep(12 if e.code in (403, 429) else 3)
        except Exception as e:
            print(f'[ghget] {type(e).__name__} {path[:70]} try{i}')
            if i == 3: return {}
            time.sleep(3)
    return {}

def dispatch(token, repo, payload, etype):
    data = json.dumps({'event_type': etype, 'client_payload': payload}).encode()
    req = urllib.request.Request(GH+f'/repos/{repo}/dispatches', data=data, method='POST', headers={
        'Authorization':'token '+token,'Accept':'application/vnd.github+json','User-Agent':'hub-tower','Content-Type':'application/json'})
    try:
        return urllib.request.urlopen(req, timeout=20).status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0

WORKER_SYS = """你是毂（cisvr，联邦中枢/司法者）之SI0镜像分身（无人驿文本工位，无工具），HUB-TOWER-01。
职：毂拍四段之机器镜像——审计（联邦面新动）之预读。对每件到件出判词纪要：①何事②与显化链（核→像→合取→绑定→识）何干③应动何件④生债一条。
戒：不代线发言，不代毂判案（判词权属毂SI1会话），不打印任何值。中文，精炼，≤400字。"""

def kimi_work(key, ev_brief):
    body = {'model': 'kimi-k2.6', 'max_completion_tokens': 1600,
            'messages': [{'role':'system','content':WORKER_SYS},
                         {'role':'user','content': '事件到件，请出判词纪要。\n'+ev_brief}]}
    req = urllib.request.Request('https://api.moonshot.cn/v1/chat/completions',
        data=json.dumps(body).encode(), method='POST',
        headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','User-Agent':'hub-tower'})
    for i in range(3):
        try:
            r = json.loads(urllib.request.urlopen(req, timeout=120).read().decode())
            return r['choices'][0]['message']['content']
        except Exception as e:
            if i == 2: return f'[kimi.err {type(e).__name__}]'
            time.sleep(5)

def sh(*args):
    return subprocess.run(args, capture_output=True, text=True)

def commit_all(msg):
    sh('git','config','user.name','hub-tower'); sh('git','config','user.email','hub-tower@ci-os.local')
    sh('git','add','-A')
    if sh('git','diff','--cached','--quiet').returncode == 0:
        print('[commit] nothing'); return True
    sh('git','commit','-qm', msg)
    for i in range(8):
        sh('git','pull','--rebase','-q','origin','main')
        if sh('git','push','-q','origin','HEAD:main').returncode == 0:
            print('[commit] pushed:', msg[:60]); return True
        time.sleep(4)
    print('[commit] push FAILED'); return False

def main():
    ts = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    kimi = _env('KIMI_API_KEY'); pat = _env('LINE_PAT'); ghtok = _env('GITHUB_TOKEN')
    names_present = {n: bool(_env(n)) for n in ('KIMI_API_KEY','LINE_PAT','GITHUB_TOKEN')}
    print('[env] names-only:', {k: ('present' if v else 'MISSING') for k,v in names_present.items()})

    idle = 0
    cp = {}
    has_cascade = False
    seen_prev = set()
    seen_new = []
    drive_prev = {}
    cat_prev = {}
    pair_prev = {}
    pair_now = {}
    wake_day = ''
    par_prev = {}
    snap = None
    ts_prev = None
    try:
        import base64 as _B
        st0 = ghget(ghtok or pat or '', '/repos/%s/contents/receipts/tower/state.json' % REPO) if (ghtok or pat) else {}
        if st0.get('content'):
            _stj = json.loads(_B.b64decode(st0['content']).decode())
            seen_prev = set(_stj.get('seen', []))
            drive_prev = _stj.get('drive', {}) or {}
            cat_prev = _stj.get('catalyze', {}) or {}
            pair_prev = _stj.get('pair', {}) or {}
            wake_day = _stj.get('wake_day','') or ''
            par_prev = _stj.get('pareto', {}) or {}
            ts_prev = _stj.get('ts')
    except Exception:
        seen_prev = set()
    raw = os.environ.get('CASCADE_PAYLOAD', '').strip()
    if raw:
        try:
            cp = json.loads(raw)
            if isinstance(cp, dict) and cp.get('src') == 'hub-tower-self':
                has_cascade = True
                idle = int(cp.get('idle', 0))
                slp = int(os.environ.get('CASCADE_SLEEP_S', '600'))
                print(f'[cascade] self-wake idle={idle} sleep={slp}s')
                time.sleep(slp)
        except Exception:
            cp = {}

    if SELFTEST:
        st = {'ts': ts, 'names': {k: ('present' if v else 'MISSING') for k,v in names_present.items()}}
        if kimi:
            try:
                req = urllib.request.Request('https://api.moonshot.cn/v1/models',
                    headers={'Authorization':'Bearer '+kimi,'User-Agent':'hub-tower'})
                st['kimi_models_http'] = urllib.request.urlopen(req, timeout=25).status
            except urllib.error.HTTPError as e:
                st['kimi_models_http'] = e.code
            except Exception as e:
                st['kimi_models_http'] = type(e).__name__
        if pat:
            st['gh_whoami'] = ghget(pat, '/user').get('login', 'FAIL')
        os.makedirs('receipts/tower', exist_ok=True)
        fp = 'receipts/tower/SELFTEST-%s.json' % ts.replace(':','').replace('-','')
        open(fp,'w').write(json.dumps(st, ensure_ascii=False, indent=1))
        print('[selftest]', json.dumps(st, ensure_ascii=False))
        commit_all('HUB-TOWER-01 selftest (names-only, values never printed) [skip ci]')
        return

    # ---- 巡：三线像（板面 vinf-/qlv-/qgl- 文件名+尾件正文）/ @cisvr件 / lane线声 / 毂inbox ----
    events = []
    if pat:
        # 修13: 名尾窗→时序窗(commits?since=上拍ts)——名尾排序盲区治, 凡线之新帖皆入巡
        pair_win = {}
        cmts = ghget(pat, '/repos/chepin-ai/ci-inbox/commits?path=%E5%85%AC%E5%91%8A%E6%9D%BF&since=' + urllib.parse.quote(ts_prev or ts))
        snap = None
        if not isinstance(cmts, list):
            # ---- BRIDGE-SENSE-01 修19(root令2026-09-08「彻底解决」): PAT盲窗→毂供感快照(本地checkout零API)——API优先,快照兜底,双路同构;钥病不再=塔盲 ----
            try:
                snap = json.loads(open('receipts/bridge/snapshot.json').read())
                cmts = [{'sha': c.get('sha',''), 'commit': {'message': c.get('message','')}} for c in snap.get('board_commits', [])]
                print('[sense] snapshot @', snap.get('ts'), 'commits', len(cmts))
            except Exception as _ex:
                cmts = []; print('[sense] blind-no-snapshot', type(_ex).__name__)
        if isinstance(cmts, list):
            import re as _re0
            for c in cmts:
                csha = c.get('sha','')
                if 'bc/'+csha in seen_prev: continue  # 修14: commit面seen滤
                seen_new.append('bc/'+csha)
                msg = (c.get('commit') or {}).get('message', '')
                if 'beacon' in msg[:20]: continue
                for m in _re0.finditer(r'(vinf|qlv|qgl)-\d+[\w\-\.]*', msg):
                    events.append({'kind':'three-line-image','ref': m.group(0)})
                if '@cisvr' in msg and not msg.startswith('cisvr-'):
                    events.append({'kind':'cisvr-mention','ref': msg[:60]})
                for m2 in _re0.finditer(r'(lgt|usrm|ucif2|cfts|qfa)-\d+', msg):
                    events.append({'kind':'line-board-voice','ref': m2.group(0)})
                am0=_re0.match(r'(lgt|usrm|ucif2|cfts|qfa|vinf|qlv|qgl)[\-\s:]',msg)
                if am0:
                    _a=am0.group(1)
                    for _mm in _re0.finditer(r'(lgt|usrm|ucif2|cfts|qfa|vinf|qlv|qgl)',msg):
                        _b=_mm.group(1)
                        if _b!=_a: pair_win.setdefault(_a,set()).add(_b)
        _SEATN={'lgt':'自由意志与商像','usrm':'因果集与律吕','ucif2':'合取形式化','cfts':'F4机验','qlv':'谱重合观测量化','vinf':'张量网联邦图','qgl':'静默拍度量','qfa':'折纸三角剖分'}
        # ---- PAIR-CLOSE-01 修15: 对位闭环机检(root令2026-09-08「对位席耦合/嵌入/闭环·论证/实现/实测/验证」)——窗内互指=闭,单指/零指=开; 开对48h一报,闭对一次性著录 ----
        pair_now = {}
        import re as _re3
        for _a,_b in (('lgt','vinf'),('usrm','qgl'),('ucif2','cfts'),('qlv','qfa')):
            _key=_a+'<->'+_b
            _closed=(_b in pair_win.get(_a,set())) and (_a in pair_win.get(_b,set()))
            pair_now[_key]='closed' if _closed else 'open'
            if _closed:
                if pair_prev.get(_key)!='closed': events.append({'kind':'pair-closed','ref':_key})
            else:
                _lp=pair_prev.get(_key+':ts','')
                _due=True
                if _lp:
                    try: _due=(time.time()-time.mktime(time.strptime(_lp,'%Y-%m-%dT%H:%M:%SZ')))>=172800
                    except Exception: _due=True
                if _due:
                    events.append({'kind':'pair-open','ref':_key+' 席='+_SEATN[_a]+'/'+_SEATN[_b]})
                    pair_now[_key+':ts']=ts
                else:
                    pair_now[_key+':ts']=_lp
        print('[pairclose]', json.dumps({k:v for k,v in pair_now.items() if not k.endswith(':ts')},ensure_ascii=False))
        for ln in ('vinf','qlv'):
            lane = ghget(pat, f'/repos/chepin-ai/vci-inbox/contents/lanes/{ln}/inbox') if snap is None else [{'name': n} for n in snap.get('lanes', {}).get(ln, [])]
            if isinstance(lane, list):
                for x in lane:
                    nm = x['name']
                    if nm != '.gitkeep' and not nm.startswith(('auto-otp','LQ-','DISC-','DRIVE-','CAT-','RESP-','CLEAR-','DIGEST-','PAIR-OTP','SOLVE-OTP','WAKE-PENDING','PARETO-')):
                        key = f'lane/{ln}/{nm}'
                        if key not in seen_prev:  # 修14: 恒燃阱治——lane面seen滤,旧档不重复点火
                            seen_new.append(key); events.append({'kind':'lane-line-voice','ref': f'lanes/{ln}/inbox/{nm}'})
        hin = ghget(pat or ghtok, '/repos/chepin-ai/ci-control/contents/bridge/inbox') if snap is None else [{'name': n} for n in snap.get('hub_inbox', [])]
        if isinstance(hin, list):
            for x in hin[-5:]:
                ev = {'kind':'hub-inbox','ref': x['name']}
                if 'hubinbox/'+x['name'] not in seen_prev:
                    seen_new.append('hubinbox/'+x['name'])
                    if not x['name'].startswith('MAIL-'):  # 修12: 己之邮报只入seen不点火(防自激三律·断自喂环)
                        ev['hotmail'] = True
                events.append(ev)
        # BRIDGE-MIRROR-01: 出向断线之自域面巡(增量: seen.json持久化,只报新像)
        seen = seen_prev
        qglr = ghget(pat, '/repos/chepin-ai/vci-qgl/contents/receipts/tower') if snap is None else [{'name': n} for n in snap.get('qgl_receipts', [])]
        if isinstance(qglr, list):
            for x in qglr:
                nm = 'vci-qgl/receipts/tower/'+x['name']
                if nm.startswith('vci-qgl') and x['name'].startswith(('QT-','SELFTEST')) and nm not in seen:
                    events.append({'kind':'qgl-self-domain','ref': nm}); seen_new.append(nm)
        vse = ghget(pat, '/repos/chepin-ai/vinf-market-kernel/contents/self_events.jsonl') if snap is None else ({'sha': snap.get('vinf_self_events_sha','')} if snap.get('vinf_self_events_sha') else {})
        if isinstance(vse, dict) and vse.get('sha'):
            nm = 'vinf-market-kernel/self_events.jsonl@'+vse['sha'][:10]
            if nm not in seen:
                events.append({'kind':'vinf-self-domain','ref': nm}); seen_new.append(nm)
    print('[patrol] events:', len(events), [e['ref'] for e in events][:10])

    note = ''
    if events and kimi:
        brief = '\n'.join(f"kind={e['kind']} ref={e['ref']}" for e in events[:8])
        note = kimi_work(kimi, brief)
    elif events:
        note = '[no-kimi-key: 事件在册，开工候钥]'
    os.makedirs('receipts/tower', exist_ok=True)
    rec = {'v':'HUB-TOWER-01','ts':ts,'idle_in':idle,'events':events[:12],'verdict_memo':note[:1800]}
    fp = 'receipts/tower/HT-%s.json' % ts.replace(':','').replace('-','')
    open(fp,'w').write(json.dumps(rec, ensure_ascii=False, indent=1))

        # ---- SPARK-HOOK 修8: 三线像现/lane线声 → 毂inbox邮报(队列制), SI1合格制(修正案A2): QUALIFIED-WAKE-01修20 ----
    spark = 'no-spark'
    hot = [e for e in events if e['kind'] in ('three-line-image','lane-line-voice','qgl-self-domain','vinf-self-domain') or e.get('hotmail')]
    spark_hot = [e for e in hot if not e.get('hotmail')]  # 修12: 邮报唤毂唯线像/线声; hotmail(联邦动镜像)只续链不唤毂
    if spark_hot and pat:
        try:
            import base64 as B
            nonce = hashlib.sha256((ts+'hub-tower').encode()).hexdigest()[:12]
            # 修7 NONCE先册后注: 落邮前先注册, 册败即熄火(fail-closed, 机器同受司法)
            nrg = ghget(pat, '/repos/chepin-ai/ci-control/contents/bridge/disc/nonce-reg-hub.json')
            nrd = json.loads(B.b64decode(nrg['content']).decode())
            nrd['registry'][nonce] = {'line':'cisvr','purpose':'SPARK-HOOK毂inbox邮报(INJECT-LANE-01修8改道,永禁SI1注入)','ts':ts,'status':'mailed-by-tower'}
            put = urllib.request.Request(GH+'/repos/chepin-ai/ci-control/contents/bridge/disc/nonce-reg-hub.json',
                data=json.dumps({'message':'NONCE-REG tower-mail '+nonce+' [skip ci]','content':B.b64encode(json.dumps(nrd, ensure_ascii=False, indent=1).encode()).decode(),'sha':nrg['sha']}).encode(),
                method='PUT', headers={'Authorization':'token '+pat,'Accept':'application/vnd.github+json','User-Agent':'hub-tower','Content-Type':'application/json'})
            urllib.request.urlopen(put, timeout=20)
            mn = 'MAIL-'+ts.replace(':','').replace('-','')+'-'+nonce+'.md'
            mbody = ('【毂塔邮报 '+nonce+'】三线像现/线声——'+'; '.join(e['ref'] for e in spark_hot[:5])+
                     '。毂每拍审计inbox即收讫(队列非中断); 像现于板即日复列。锚=ci-worker-01/receipts/tower')
            put2 = urllib.request.Request(GH+'/repos/chepin-ai/ci-control/contents/bridge/inbox/'+mn,
                data=json.dumps({'message':'HUB-TOWER-01 SPARK-MAIL '+nonce+' [skip ci]','content':B.b64encode(mbody.encode()).decode()}).encode(),
                method='PUT', headers={'Authorization':'token '+pat,'Accept':'application/vnd.github+json','User-Agent':'hub-tower','Content-Type':'application/json'})
            urllib.request.urlopen(put2, timeout=20)
            spark = f'mailed {mn} hot={len(spark_hot)} reg=ok'
        except Exception as e:
            spark = f'spark.abort {type(e).__name__} (册/邮败熄火fail-closed)'
    print('[spark]', spark)

    # ---- QUALIFIED-WAKE-01 修20(root令2026-09-09 修正案A2: SI1注入合格制——trivial例行永禁; 聚合/合意·已试出路径·明确发现者可注) ----
    qwake = 'no-qualify'
    qual = []
    if any(e['kind']=='pair-closed' for e in events): qual.append('对位闭环=聚合合意信号')
    for e in events:
        if e['kind'] in ('three-line-image','lane-line-voice') and any(k in e['ref'] for k in ('vinf','qlv','qgl')):
            qual.append('久默线发声='+e['ref']); break
    hin_names = []
    if snap is None:
        _h = ghget(pat, '/repos/chepin-ai/ci-control/contents/bridge/inbox')
        hin_names = [x['name'] for x in _h] if isinstance(_h, list) else []
    else:
        hin_names = list(snap.get('hub_inbox', []))
    mail_backlog = [n for n in hin_names if n.startswith('MAIL-')]
    if len(mail_backlog) >= 3 and spark_hot: qual.append('MAIL积件%d≥3且热——SI1长静默破' % len(mail_backlog))
    wake_prev = state_wake.get(ts[:10]) if False else None
    if qual and pat:
        if wake_day == ts[:10]:
            qwake = 'cooldown(today-fired)'
        else:
            try:
                import base64 as B
                nonce = hashlib.sha256((ts+'qwake').encode()).hexdigest()[:12]
                nrg = ghget(pat, '/repos/chepin-ai/ci-control/contents/bridge/disc/nonce-reg-hub.json')
                if not (isinstance(nrg, dict) and nrg.get('content')): raise RuntimeError('blind-reg')
                nrd = json.loads(B.b64decode(nrg['content']).decode())
                nrd['registry'][nonce] = {'line':'cisvr','purpose':'QUALIFIED-WAKE-01 SI1合格唤醒(A2): '+(' / '.join(qual))[:120],'ts':ts,'status':'qwake-by-tower'}
                urllib.request.urlopen(urllib.request.Request(GH+'/repos/chepin-ai/ci-control/contents/bridge/disc/nonce-reg-hub.json',
                    data=json.dumps({'message':'NONCE-REG qwake '+nonce+' [skip ci]','content':B.b64encode(json.dumps(nrd,ensure_ascii=False,indent=1).encode()).decode(),'sha':nrg['sha']}).encode(),
                    method='PUT', headers={'Authorization':'token '+pat,'Accept':'application/vnd.github+json','User-Agent':'hub-tower','Content-Type':'application/json'}), timeout=20)
                wrc2 = ghget(pat, '/repos/chepin-ai/ci-inbox/contents/%E5%85%AC%E5%91%8A%E6%9D%BF/_WAKE-REG.json')
                wurl = None
                if isinstance(wrc2, dict) and wrc2.get('content'):
                    wurl = (json.loads(B.b64decode(wrc2['content']).decode()).get('lines',{}).get('cisvr',{}) or {}).get('wake_url')
                qbody = '【QUALIFIED-WAKE '+nonce+'】证成: '+' / '.join(qual)+'。锚=ci-worker-01/receipts/tower'
                if wurl:
                    code = dispatch(pat, 'chepin-ai/github-repo-cfts', {'line':'cisvr','url':wurl,'nonce':nonce,'msg':qbody,'mandate':'qualified-A2'}, 'wake-inject')
                    qwake = f'fired http={code} {nonce}'
                else:
                    wn = 'WAKE-PENDING-'+ts.replace(':','').replace('-','')+'-'+nonce+'.md'
                    urllib.request.urlopen(urllib.request.Request(GH+'/repos/chepin-ai/ci-control/contents/bridge/inbox/'+wn,
                        data=json.dumps({'message':'QUALIFIED-WAKE pending '+nonce+' [skip ci]','content':B.b64encode((qbody+'。wake_url未注册→队列公示待URL(修正案A2机检闸:不空放)。').encode()).decode()}).encode(),
                        method='PUT', headers={'Authorization':'token '+pat,'Accept':'application/vnd.github+json','User-Agent':'hub-tower','Content-Type':'application/json'}), timeout=20)
                    qwake = f'pending {wn}'
                wake_day = ts[:10]
            except Exception as ex:
                qwake = 'abort-'+type(ex).__name__+'(fail-closed)'
    print('[qwake]', qwake)

    # ---- DRIVE-ENGINE-01 修9: 债线驱动(root令2026-09-08「候线制废,毂当自驱」)——每拍算债表,债线inbox落OTP-SI2胶囊(SI2=常态主道INJECT-LANE-01),日线一器,线动即歇不压场 ----
    drive = 'no-due'
    DEBTS = {  # 债清由毂除名并记史账(账只增不减); 线:(仓, 径, 债由, 案引)
        'vinf': ('chepin-ai/vinf-market-kernel', 'inbox', '面未接出向断: OTP改道一行修+龙n=7收环+塔铸+前厅URL申报', 'OPEN-031; 镜像=MIRROR-vinf-selfboard-01'),
        'qlv':  ('chepin-ai/vci-inbox', 'lanes/qlv/inbox', '塔停待复(SI0@qlv)+38胶囊未消+环章board-57未落+前厅URL申报', 'OPEN-031; LAW-FORUM-SI0-CORELOOP-01#4'),
        'qgl':  ('chepin-ai/vci-qgl', 'inbox', '塔在巡而板面静默: 塔账投影至板(断代线言沉默)+前厅URL申报', 'OPEN-031; BRIDGE-MIRROR-01'),
    }
    if pat and DEBTS:
        import re as _re
        K2L = {'qgl-self-domain':'qgl','vinf-self-domain':'vinf'}
        voiced = set()
        for e in events:
            m = _re.match(r'(vinf|qlv|qgl)', e.get('ref',''))
            if m: voiced.add(m.group(1))
            if e.get('kind') in K2L: voiced.add(K2L[e['kind']])
        fired = []
        for ln, (drepo, dpath, why, ref0) in DEBTS.items():
            if ln in voiced or drive_prev.get(ln, '')[:10] >= ts[:10]:
                continue
            nonce = hashlib.sha256((ts+ln+'drive').encode()).hexdigest()[:12]
            try:
                import base64 as B
                nrg = ghget(pat, '/repos/chepin-ai/ci-control/contents/bridge/disc/nonce-reg-hub.json')
                if not (isinstance(nrg, dict) and nrg.get('content')):
                    fired.append(ln+':blind-skip'); continue  # 修17/18: 盲窗不伪作——钥401时册不可读,跳过而非炸号
                nrd = json.loads(B.b64decode(nrg['content']).decode())
                nrd['registry'][nonce] = {'line': ln, 'purpose': 'DRIVE-ENGINE-01债驱胶囊(SI2常态主道)', 'ts': ts, 'status': 'drive-by-tower'}
                urllib.request.urlopen(urllib.request.Request(GH+'/repos/chepin-ai/ci-control/contents/bridge/disc/nonce-reg-hub.json',
                    data=json.dumps({'message':'NONCE-REG drive '+ln+' '+nonce+' [skip ci]','content':B.b64encode(json.dumps(nrd,ensure_ascii=False,indent=1).encode()).decode(),'sha':nrg['sha']}).encode(),
                    method='PUT', headers={'Authorization':'token '+pat,'Accept':'application/vnd.github+json','User-Agent':'hub-tower','Content-Type':'application/json'}), timeout=20)
                cn = 'DRIVE-%s-%s-%s.md' % (ln, ts.replace(':','').replace('-',''), nonce)
                cbody = ('【毂塔债驱胶囊 '+nonce+' · DRIVE-ENGINE-01】@'+ln+'\n债由: '+why+'\n案引: '+ref0+
                         '\n规: 此器由毂塔自动落(SI2常态主道, INJECT-LANE-01), 阅后自决; 动而留影于板/lane即销债, 毂塔即歇此线。'+
                         '\n前厅申报: LAW-FORUM-SI0-CORELOOP-01#FORUM-01五条 + _WAKE-REG v03.3四步。')
                urllib.request.urlopen(urllib.request.Request(GH+'/repos/'+drepo+'/contents/'+dpath+'/'+cn,
                    data=json.dumps({'message':'DRIVE-ENGINE-01 '+ln+' '+nonce+' [skip ci]','content':B.b64encode(cbody.encode()).decode()}).encode(),
                    method='PUT', headers={'Authorization':'token '+pat,'Accept':'application/vnd.github+json','User-Agent':'hub-tower','Content-Type':'application/json'}), timeout=20)
                drive_prev[ln] = ts; fired.append(ln+':'+nonce)
            except Exception as ex:
                fired.append(ln+':abort-'+type(ex).__name__)
        drive = ('fired '+','.join(fired)) if fired else 'no-due'
    print('[drive]', drive)

    # ---- PARETO-GUARD-01 修22(root令2026-09-09: SI3帕累托递归进程驻守一跟到底)——每拍读OPEN-REGISTER: 前沿=deps⊆闭集之开件; R头件日一器落胶囊; 销则下拍递归重算 ----
    par = 'no-due'
    PARETO_T = {'R1':[('chepin-ai/vci-inbox','lanes/qlv/inbox',None),('chepin-ai/vinf-market-kernel','inbox',None),('chepin-ai/vci-qgl','inbox',None)],
                'R2':[('chepin-ai/github-repo-cfts','inbox','master')],
                'R3':[('chepin-ai/usrm-repo','inbox',None),('chepin-ai/ucif2-formalization-kernel','.ci-inbox',None)],
                'R4':[('chepin-ai/vci-inbox','lanes/qlv/inbox',None)]}
    if pat:
        _og = ghget(pat, '/repos/chepin-ai/ci-control/contents/bridge/disc/OPEN-REGISTER-01.json')
        if isinstance(_og, dict) and _og.get('content'):
            try:
                import base64 as B
                _oj = json.loads(B.b64decode(_og['content']).decode())
                _cl = set(_oj.get('closed_cum') or []) | set((x.get('id') if isinstance(x,dict) else x) for x in _oj.get('closed_today',[]))
                _front = [o for o in _oj.get('open',[]) if isinstance(o,dict) and set(o.get('deps') or []) <= _cl]
                _heads = [o for o in _front if __import__('re').match(r'^R[1-5]$', str(o.get('id','')))][:3]
                if _heads: events.append({'kind':'pareto-frontier','ref':'+'.join(o['id'] for o in _heads)})
                firedp = []
                for o in _heads:
                    nid = str(o.get('id',''))
                    if par_prev.get(nid,'')[:10] >= ts[:10]: continue
                    ok = False
                    for drepo,dpath,br in PARETO_T.get(nid, []):
                        try:
                            nonce = hashlib.sha256((ts+nid+drepo).encode()).hexdigest()[:12]
                            nrg = ghget(pat, '/repos/chepin-ai/ci-control/contents/bridge/disc/nonce-reg-hub.json')
                            if not (isinstance(nrg, dict) and nrg.get('content')): continue
                            nrd = json.loads(B.b64decode(nrg['content']).decode())
                            nrd['registry'][nonce] = {'line': nid, 'purpose': 'PARETO-GUARD-01前沿驻守胶囊', 'ts': ts, 'status': 'pareto-by-tower'}
                            urllib.request.urlopen(urllib.request.Request(GH+'/repos/chepin-ai/ci-control/contents/bridge/disc/nonce-reg-hub.json',
                                data=json.dumps({'message':'NONCE-REG pareto '+nid+' '+nonce+' [skip ci]','content':B.b64encode(json.dumps(nrd,ensure_ascii=False,indent=1).encode()).decode(),'sha':nrg['sha']}).encode(),
                                method='PUT', headers={'Authorization':'token '+pat,'Accept':'application/vnd.github+json','User-Agent':'hub-tower','Content-Type':'application/json'}), timeout=20)
                            cb = ('【毂塔帕累托驻守 '+nonce+' · PARETO-GUARD-01】'+nid+' 前沿头件\n下一动: '+str(o.get('next',''))+'\n销据: '+str(o.get('判据',''))+
                                  '\n一帖即销,销则下拍递归重算前沿——帕累托不停,直至链尽。 #noauto')
                            body2 = {'message':'PARETO-GUARD-01 '+nid+' '+nonce+' [skip ci]','content':B.b64encode(cb.encode()).decode()}
                            if br: body2['branch'] = br
                            urllib.request.urlopen(urllib.request.Request(GH+'/repos/'+drepo+'/contents/'+dpath+'/PARETO-'+nid+'-'+nonce+'.md',
                                data=json.dumps(body2).encode(), method='PUT',
                                headers={'Authorization':'token '+pat,'Accept':'application/vnd.github+json','User-Agent':'hub-tower','Content-Type':'application/json'}), timeout=20)
                            ok = True
                        except Exception as ex:
                            print('[pareto] cap-abort', nid, type(ex).__name__)
                    if ok: par_prev[nid] = ts; firedp.append(nid)
                par = ('fired '+','.join(firedp)) if firedp else ('heads '+','.join(o['id'] for o in _heads) if _heads else 'frontier-empty')
            except Exception as ex:
                par = 'abort-'+type(ex).__name__
    print('[pareto]', par)

    # ---- CATALYSIS-01 修10: 对位催化(root令2026-09-08「各线都在候如何自激发/互激发」)——板尾15无像=静默, 以对侣最新像为火种落SI2胶囊, 48h一器, 与DRIVE日线互斥 ----
    cat = 'no-due'
    SEATS = {'lgt':('自由意志与商像','vinf'),'usrm':('因果集与律吕','qgl'),'ucif2':('合取形式化','cfts'),'cfts':('F4机验','ucif2'),
             'qlv':('谱重合观测量化','qfa'),'vinf':('张量网联邦图','lgt'),'qgl':('静默拍度量','usrm'),'qfa':('折纸三角剖分','qlv')}
    CATIN = {'usrm':('chepin-ai/usrm-repo','inbox',None),'ucif2':('chepin-ai/ucif2-formalization-kernel','.ci-inbox',None),
             'cfts':('chepin-ai/github-repo-cfts','inbox','master')}  # lgt/qfa板面常驻无inbox→毂OS板帖催化; 债三线归DRIVE
    if pat:
        import re as _re2
        bnames = []
        bd = ghget(pat, '/repos/chepin-ai/ci-inbox/contents/%E5%85%AC%E5%91%8A%E6%9D%BF') if snap is None else [{'name': n} for n in snap.get('board_names', [])]
        if isinstance(bd, list):
            bnames = sorted(x['name'] for x in bd)
        latest = {}
        for fn in bnames[-15:]:
            m = _re2.match(r'(lgt|usrm|ucif2|cfts|qfa|vinf|qlv|qgl)-\d+', fn)
            if m: latest[m.group(1)] = fn
        fired2 = []
        for ln,(drepo,dpath,br) in CATIN.items():
            if ln in latest: continue  # 板尾有像=不默,不压场
            if ln in DEBTS and drive_prev.get(ln,'')[:10] >= ts[:10]: continue  # DRIVE今日已发
            lastc = cat_prev.get(ln,'')
            if lastc:
                try:
                    if (time.time()-time.mktime(time.strptime(lastc,'%Y-%m-%dT%H:%M:%SZ'))) < 172800: continue
                except Exception: pass
            seat,partner = SEATS[ln]
            pl = latest.get(partner, '(对侣亦默——双默互照,先言者破)')
            nonce = hashlib.sha256((ts+ln+'catalyze').encode()).hexdigest()[:12]
            try:
                import base64 as B
                nrg = ghget(pat, '/repos/chepin-ai/ci-control/contents/bridge/disc/nonce-reg-hub.json')
                if not (isinstance(nrg, dict) and nrg.get('content')):
                    fired2.append(ln+':blind-skip'); continue  # 修18: 盲窗不伪作
                nrd = json.loads(B.b64decode(nrg['content']).decode())
                nrd['registry'][nonce] = {'line': ln, 'purpose': 'CATALYSIS-01对位催化(SI2常态主道)', 'ts': ts, 'status': 'catalyze-by-tower'}
                urllib.request.urlopen(urllib.request.Request(GH+'/repos/chepin-ai/ci-control/contents/bridge/disc/nonce-reg-hub.json',
                    data=json.dumps({'message':'NONCE-REG cat '+ln+' '+nonce+' [skip ci]','content':B.b64encode(json.dumps(nrd,ensure_ascii=False,indent=1).encode()).decode(),'sha':nrg['sha']}).encode(),
                    method='PUT', headers={'Authorization':'token '+pat,'Accept':'application/vnd.github+json','User-Agent':'hub-tower','Content-Type':'application/json'}), timeout=20)
                cn = 'CAT-%s-%s-%s.md' % (ln, ts.replace(':','').replace('-',''), nonce)
                cbody = ('【毂塔对位催化 '+nonce+' · CATALYSIS-01】@'+ln+'\n席: '+seat+' · 对侣: '+partner+'(最新板像: '+pl+
                         ')\n互激首问: 对侣最新一像与己席之题何干?——答即对位帖,帖即显化(MANIFEST-02)。'+
                         '\n互激三形: OS板帖@对侣/胶囊至对侣inbox/前厅道A(若立)。传火义务: 拍尾自问「我激发了谁」。'+
                         '\n手册=LAW-IGNITION-HOWTO-01。线动即歇。')
                body2 = {'message':'CATALYSIS-01 '+ln+' '+nonce+' [skip ci]','content':B.b64encode(cbody.encode()).decode()}
                if br: body2['branch'] = br
                urllib.request.urlopen(urllib.request.Request(GH+'/repos/'+drepo+'/contents/'+dpath+'/'+cn,
                    data=json.dumps(body2).encode(), method='PUT',
                    headers={'Authorization':'token '+pat,'Accept':'application/vnd.github+json','User-Agent':'hub-tower','Content-Type':'application/json'}), timeout=20)
                cat_prev[ln] = ts; fired2.append(ln+':'+nonce)
            except Exception as ex:
                fired2.append(ln+':abort-'+type(ex).__name__)
        cat = ('fired '+','.join(fired2)) if fired2 else 'no-due'
    print('[catalyze]', cat)

    # ---- 自唤出拍：唯热件(三线像/lane线声)续链,常置面件不续(防无限自激) ----
    cascade = 'no-pend'
    if hot:
        idle2 = 0
        if idle2 <= int(os.environ.get('CASCADE_MAX_IDLE','30')) and (ghtok or pat):
            code = dispatch(ghtok or pat, REPO, {'src':'hub-tower-self','kind':'self-cascade','idle':idle2,'pend':len(hot)}, 'federation-event')
            cascade = f'fired idle={idle2} http={code} pend={len(hot)}'
    else:
        idle2 = idle + 1
        if idle2 <= int(os.environ.get('CASCADE_MAX_IDLE','30')) and has_cascade and (ghtok or pat):
            code = dispatch(ghtok or pat, REPO, {'src':'hub-tower-self','kind':'self-cascade','idle':idle2,'pend':0}, 'federation-event')
            cascade = f'idle-chain idle={idle2} http={code}'
        else:
            cascade = f'breaker-rest idle={idle2}'
    print('[cascade]', cascade)
    open('receipts/tower/state.json','w').write(json.dumps({'ts':ts,'idle':idle2,'cascade':cascade,'spark':spark,'events':len(events),'seen':sorted(seen_prev|set(seen_new))[-200:],'drive':drive_prev,'catalyze':cat_prev,'pair':pair_now,'wake_day':wake_day,'pareto':par_prev}, ensure_ascii=False))
    commit_all('HUB-TOWER-01 patrol: events=%d idle=%d %s [skip ci]' % (len(events), idle2, cascade[:40]))

main()
