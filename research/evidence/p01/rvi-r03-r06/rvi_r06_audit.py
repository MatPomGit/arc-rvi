"""Independent comparison on immutable R05 artifact. Requires rvi_oracle_audit.py."""
import json, sys, hashlib
from pathlib import Path
from zipfile import ZipFile
from collections import defaultdict
from math import fsum, hypot, ulp, isclose
from rvi_oracle_audit import transition, visible, angle
OLD=('fixed_order','greedy_coverage','greedy_distance','fixed_weight','fuzzy_budget')
NEW=('feasible_greedy','gain_per_cost','receding_horizon_2','receding_horizon_3')

def evaluate(s,m):
    route=s['route']; areas={p['identifier']:p['area_m2'] for p in s['patches']}; required=set(areas); total=fsum(areas.values()); views=[visible(s,v) for v in route]
    covered=set(); remaining=tuple(range(len(route))); pos=s['start']; t=dist=0.; chosen=[]; failure=None; expanded=0
    def area(ids): return fsum(areas[k] for k in sorted(ids))
    def choose_horizon(pos,t,covered,remaining,h):
        nonlocal expanded
        best=None; best_seq=()
        def visit(pos,tt,c,avail,seq):
            nonlocal best,best_seq,expanded
            if seq and c!=covered:
                key=(-area(c),tt,len(seq),seq)
                if best is None or key<best: best=key;best_seq=seq
            if len(seq)==h or c==required: return
            for i in avail:
                expanded+=1; reason,nt,_=transition(s,pos,route[i],tt)
                if not reason: visit(route[i],nt,c|views[i],tuple(j for j in avail if j!=i),seq+(i,))
        visit(pos,t,covered,remaining,());return best_seq[0] if best_seq else None
    while covered!=required:
        if m.startswith('receding_horizon'):
            i=choose_horizon(pos,t,covered,remaining,int(m[-1]))
        elif m in NEW:
            options=[]
            for j in remaining:
                expanded+=1; reason,nt,_=transition(s,pos,route[j],t); gain=area(views[j]-covered); cost=nt-t
                if reason or gain<=0: continue
                # Zero-cost actions rank first, and no infinite value is serialized.
                key=(gain,-cost,-j) if m=='feasible_greedy' else (cost==0,gain/cost if cost else 0,gain,-cost,-j)
                options.append((key,j))
            i=max(options)[1] if options else None
        else:
            eligible=[j for j in remaining if m=='fixed_order' or views[j]-covered]
            def rank(j):
                gain=len(views[j]-covered); d=hypot(route[j]['x']-pos['x'],route[j]['y']-pos['y']); motion=s['motion']
                if m=='greedy_coverage':return (gain,)
                if m=='greedy_distance':return (gain/(1+d),gain,-d)
                cost=d/motion['linear_speed_m_s']+angle(route[j]['yaw_rad'],pos['yaw_rad'])/motion['angular_speed_rad_s']+motion['capture_duration_s']; b=motion['max_time_s']; u=min(1,t/b) if b else 1
                weight=.8-.4*u if m=='fuzzy_budget' else .6
                return (weight*gain/len(required-covered)+(1-weight)*(1-min(1,cost/b)),gain,-d)
            i=(eligible[0] if m=='fixed_order' else max(eligible,key=rank)) if eligible else None
        if i is None: failure='no_feasible_positive_gain_plan' if m in NEW else 'unreachable_regions';break
        reason,nt,nd=transition(s,pos,route[i],t); chosen.append(i+1); remaining=tuple(j for j in remaining if j!=i)
        if reason: failure=reason;break
        pos=route[i]; t=nt;dist+=nd;covered|=views[i]
    return dict(method=m,success=covered==required,coverage=area(covered)/total,elapsed_s=t,travel_m=dist,route=chosen,failure_reason=failure,expanded_transitions=expanded if m in NEW else None)

def run(path):
    with ZipFile(path) as z:
        names=z.namelist();assert not any('/holdout/' in n or '/development/' in n for n in names)
        hashes={line.split()[1].removeprefix('./'):line.split()[0] for line in z.read('SHA256SUMS').decode().splitlines()};assert set(hashes)==set(names)-{'SHA256SUMS'};assert all(hashlib.sha256(z.read(n)).hexdigest()==h for n,h in hashes.items()); raw=z.read('decision-population.json');d=json.loads(raw); source=z.read('source-sha.txt').decode().strip()
    rows=[]; ids=set()
    for row in d['rows']:
        for case in row['cases']:
            s=case['scene'];o=case['oracle']; sid=s['scene_id']; assert sid not in ids;ids.add(sid)
            assert hashlib.sha256(json.dumps(s,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()==case['scene_sha256']
            # Replay optimal witness against independent transitions/visibility.
            pos=s['start'];t=0;cov=set();areas={p['identifier']:p['area_m2'] for p in s['patches']}
            for i in o['optimal_route']:
                v=s['route'][i-1]; reason,t,_=transition(s,pos,v,t);assert reason is None;pos=v;cov|=visible(s,v)
            assert isclose(t,o['optimal_elapsed_s'],abs_tol=1e-12);assert isclose(fsum(areas[k] for k in cov)/fsum(areas.values()),o['optimal_coverage'],abs_tol=1e-12)
            for m in OLD+NEW:
                res=evaluate(s,m);gap=o['optimal_coverage']-res['coverage'];assert gap>=-1e-12 and (not res['success'] or o['full_feasible'])
                time_gap=res['elapsed_s']-o['full_min_time_s'] if res['success'] else None
                assert time_gap is None or time_gap>=-1e-10
                rows.append(dict(scene_id=sid,family=row['family'],ratio=case['budget_ratio'],feasible=o['full_feasible'],order_sensitive=(case['first_action_dead_end_fraction'] or 0)>0,gap=max(0,gap),time_gap=time_gap,**res))
    assert len(ids)==192 and len(rows)==1728
    def summary(g):
        n=len(g);f=sum(r['feasible'] for r in g);success=sum(r['success'] for r in g); tg=[r['time_gap'] for r in g if r['success']];ex=[r['expanded_transitions'] for r in g if r['expanded_transitions'] is not None]
        return dict(trials=n,feasible=f,success=success,avoidable=f-success,afr=(f-success)/f if f else None,mean_gap=fsum(r['gap'] for r in g)/n,mean_full_time_gap=fsum(tg)/len(tg) if tg else None,mean_expanded=fsum(ex)/len(ex) if ex else None)
    summaries={m:summary([r for r in rows if r['method']==m]) for m in OLD+NEW}
    by_ratio={str(b):{m:summary([r for r in rows if r['method']==m and r['ratio']==b]) for m in OLD+NEW} for b in (.8,1.05,1.4)}
    by_family={f:{m:summary([r for r in rows if r['method']==m and r['family']==f]) for m in OLD+NEW} for f in sorted({r['family'] for r in rows})}
    return dict(source_sha=source,archive_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),population_sha256=hashlib.sha256(raw).hexdigest(),checksums=len(hashes),summary=summaries,by_ratio=by_ratio,by_family=by_family,rows=rows)
if __name__=='__main__':
    result=run(sys.argv[1]);Path(sys.argv[2]).write_text(json.dumps(result,indent=2,allow_nan=False)+'\n'); print(json.dumps({k:v for k,v in result.items() if k not in ('rows','by_family')},indent=2))
