# hub_tower.py — HUB-TOWER-01 · 毂SI0镜像分身（TOWER-PARADIGM-01第四移植：qlv→qgl→[vinf候]→hub）
# 纯事件驱动：无定时器；外部唤起（push|issues|issue_comment|repository_dispatch|workflow_dispatch）
# 职：巡联邦面（板面三线像/@cisvr件/lane线声/毂inbox）→ 判词纪要落账 → 三线像现或急件→SPARK-HOOK唤毂（otp-gate wake-inject@cisvr）→ 有候件自唤下拍
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
    try:
        import base64 as _B
        st0 = ghget(ghtok or pat or '', '/repos/%s/contents/receipts/tower/state.json' % REPO) if (ghtok or pat) else {}
        if st0.get('content'):
            seen_prev = set(json.loads(_B.b64decode(st0['content']).decode()).get('seen', []))
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
        board = ghget(pat, '/repos/chepin-ai/ci-inbox/contents/%E5%85%AC%E5%91%8A%E6%9D%BF')
        if isinstance(board, list):
            names = sorted(x['name'] for x in board)
            for fn in names[-15:]:
                if re3 := __import__('re').match(r'(vinf|qlv|qgl)-\d+', fn):
                    events.append({'kind':'three-line-image','ref': fn})
            for fn in names[-5:]:
                if fn.startswith('_'): continue
                c = ghget(pat, '/repos/chepin-ai/ci-inbox/contents/%E5%85%AC%E5%91%8A%E6%9D%BF/' + urllib.parse.quote(fn))
                if c.get('content'):
                    import base64 as B
                    txt = B.b64decode(c['content']).decode(errors='replace')
                    if '@cisvr' in txt:
                        events.append({'kind':'cisvr-mention','ref': fn})
        for ln in ('vinf','qlv'):
            lane = ghget(pat, f'/repos/chepin-ai/vci-inbox/contents/lanes/{ln}/inbox')
            if isinstance(lane, list):
                for x in lane:
                    nm = x['name']
                    if nm != '.gitkeep' and not nm.startswith('auto-otp') and not nm.startswith('LQ-') and not nm.startswith('DISC-'):
                        events.append({'kind':'lane-line-voice','ref': f'lanes/{ln}/inbox/{nm}'})
        hin = ghget(pat or ghtok, '/repos/chepin-ai/ci-control/contents/bridge/inbox')
        if isinstance(hin, list):
            for x in hin[-5:]:
                events.append({'kind':'hub-inbox','ref': x['name']})
        # BRIDGE-MIRROR-01: 出向断线之自域面巡(增量: seen.json持久化,只报新像)
        seen = seen_prev
        qglr = ghget(pat, '/repos/chepin-ai/vci-qgl/contents/receipts/tower')
        if isinstance(qglr, list):
            for x in qglr:
                nm = 'vci-qgl/receipts/tower/'+x['name']
                if nm.startswith('vci-qgl') and x['name'].startswith(('QT-','SELFTEST')) and nm not in seen:
                    events.append({'kind':'qgl-self-domain','ref': nm}); seen_new.append(nm)
        vse = ghget(pat, '/repos/chepin-ai/vinf-market-kernel/contents/self_events.jsonl')
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

    # ---- SPARK-HOOK：三线像现/lane线声 → 唤毂（otp-gate wake-inject@cisvr），每拍至多一发 ----
    spark = 'no-spark'
    hot = [e for e in events if e['kind'] in ('three-line-image','lane-line-voice','qgl-self-domain','vinf-self-domain')]
    # LAW-INJECT-LANE-01码级硬约束: SPARK-HOOK合法目标白名单=('cisvr',)——唤毂=自举例外;他线SI1永禁注入
    SPARK_WHITELIST = ('cisvr',)
    if hot and pat and 'cisvr' in SPARK_WHITELIST:
        wr = ghget(pat, '/repos/chepin-ai/ci-inbox/contents/%E5%85%AC%E5%91%8A%E6%9D%BF/_WAKE-REG.json')
        try:
            import base64 as B
            wurl = json.loads(B.b64decode(wr['content']).decode())['lines']['cisvr']['wake_url']
            nonce = hashlib.sha256((ts+'hub-tower').encode()).hexdigest()[:12]
            # 修7 NONCE先册后注入机: 点火前先注册nonce-reg-hub, 册败即熄火(fail-closed, 机器同受司法)
            nrg = ghget(pat, '/repos/chepin-ai/ci-control/contents/bridge/disc/nonce-reg-hub.json')
            nrd = json.loads(B.b64decode(nrg['content']).decode())
            nrd['registry'][nonce] = {'line':'cisvr','purpose':'SPARK-HOOK唤毂(毂塔自举例外)','ts':ts,'status':'fired-by-tower'}
            put = urllib.request.Request(GH+'/repos/chepin-ai/ci-control/contents/bridge/disc/nonce-reg-hub.json',
                data=json.dumps({'message':'NONCE-REG tower-spark '+nonce+' [skip ci]','content':B.b64encode(json.dumps(nrd, ensure_ascii=False, indent=1).encode()).decode(),'sha':nrg['sha']}).encode(),
                method='PUT', headers={'Authorization':'token '+pat,'Accept':'application/vnd.github+json','User-Agent':'hub-tower','Content-Type':'application/json'})
            urllib.request.urlopen(put, timeout=20)
            code = dispatch(pat, 'chepin-ai/github-repo-cfts',
                {'line':'cisvr','url':wurl,'nonce':nonce,
                 'msg':'毂塔镜像: 三线像现——'+';'.join(e['ref'] for e in hot[:3])+'。收讫接应即日复列。锚=ci-worker-01/receipts/tower',
                 'mandate':'true'}, 'wake-inject')
            spark = f'fired http={code} hot={len(hot)} reg=ok'
        except Exception as e:
            spark = f'spark.abort {type(e).__name__} (册败熄火/先册后注)'
    print('[spark]', spark)

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
    open('receipts/tower/state.json','w').write(json.dumps({'ts':ts,'idle':idle2,'cascade':cascade,'spark':spark,'events':len(events),'seen':sorted(seen_prev|set(seen_new))[-200:]}, ensure_ascii=False))
    commit_all('HUB-TOWER-01 patrol: events=%d idle=%d %s [skip ci]' % (len(events), idle2, cascade[:40]))

main()
