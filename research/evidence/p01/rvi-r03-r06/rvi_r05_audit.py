"""Independent, policy-free structural population audit (RVI-R05)."""
from collections import Counter
from itertools import combinations
from math import pi, sin, cos, remainder, radians, fsum, ulp
from random import Random
import json
from pathlib import Path
from rvi_oracle_audit import visible, blocked, transition

SEED = 20261125
RATIOS = (0.8, 1.05, 1.4)

def pose(r, a, yaw):
    return dict(x=r*cos(a), y=r*sin(a), yaw_rad=remainder(yaw, 2*pi))

def families():
    rng=Random(SEED)
    for i in range(8):
        phase=rng.uniform(-pi,pi)
        patches=[]
        for j in range(6):
            angle=phase+j*pi/3+rng.uniform(-.16,.16)
            p=pose(rng.uniform(1.15,1.45),angle,angle)
            patches.append(dict(identifier=f'p{j+1}',x=p['x'],y=p['y'],normal_rad=p['yaw_rad'],area_m2=rng.uniform(.6,1.4)))
        views=[]
        for j in range(8):
            angle=phase+(j*pi/3 if j<6 else (j-6+.5)*pi)+rng.uniform(-.16,.16)
            views.append(pose(rng.uniform(2.65,3.35),angle,angle+pi+rng.uniform(-.10,.10)))
        order=list(range(8));rng.shuffle(order)
        start=pose(3.5,phase-.35,phase+pi-.35)
        for n in (6,8):
            for fov in (18,55):
                for obstacle in (False,True):
                    route=[views[j] for j in order if j<n]
                    yield dict(scene_id=f'decision_dev_{i+1:03d}_n{n}_f{fov}_o{int(obstacle)}',start=start,route=route,patches=patches,obstacles=[dict(x=0.,y=0.,radius_m=.85)] if obstacle else [],camera=dict(horizontal_fov_rad=radians(fov),min_range_m=.1,max_range_m=6.,max_incidence_rad=radians(75)),motion=dict(linear_speed_m_s=1.,angular_speed_rad_s=1.5,robot_radius_m=.15,capture_duration_s=.25,max_time_s=100.)), i+1,n,fov,obstacle

def analyze(scene):
    n=len(scene['route']); views=scene['route']; poses=[scene['start'],*views]; sets=[visible(scene,v) for v in views]; required={p['identifier'] for p in scene['patches']}
    costs={}; all_edges=0; blocked_edges=0
    for i,p in enumerate(poses):
        for j,v in enumerate(views,1):
            if i==j: continue
            reason,c,_=transition(scene,p,v,0)
            if reason=='path_collision':
                if i: blocked_edges+=1
            elif reason is None: costs[i,j]=c
            else: raise ValueError(reason)
            if i: all_edges+=1
    first={}; best={}; full=None
    def walk(i,used,covered,t,seq):
        nonlocal full
        if covered==required:
            if full is None or t<full: full=t
            first[seq[0]]=min(first.get(seq[0],float('inf')),t)
            return
        for j in range(1,n+1):
            if j not in used and (i,j) in costs:
                walk(j,used|{j},covered|sets[j-1],t+costs[i,j],seq+(j,))
    walk(0,set(),set(),0.,())
    unions=[len(a|b) for a,b in combinations(sets,2)]
    similarities=[len(a&b)/len(a|b) for a,b in combinations(sets,2) if a|b]
    minimum=next((k for k in range(1,n+1) if any(set().union(*c)==required for c in combinations(sets,k))),None)
    ref=full if full is not None else n*max(costs.values(),default=1.)
    def feasible(t,b): return t<=b or t-b<=8*max(ulp(t),ulp(b))
    rows=[]
    for ratio in RATIOS:
        budget=ref*ratio
        immediate=[j for j in range(1,n+1) if (0,j) in costs and feasible(costs[0,j],budget)]
        valid=[j for j,t in first.items() if feasible(t,budget)]
        rows.append(dict(ratio=ratio,budget_s=budget,full_feasible=bool(valid),first_immediate=len(immediate),first_full=len(valid),dead_end_fraction=(len(immediate)-len(valid))/len(immediate) if valid else None))
    return dict(min_full_time_s=full,minimum_views=minimum,mean_jaccard=fsum(similarities)/len(similarities) if similarities else None,blocked_edge_fraction=blocked_edges/all_edges,coverage_union=len(set().union(*sets))/len(required),cases=rows)

def main():
    rows=[]
    for s,f,n,fov,o in families(): rows.append(dict(family=f,n=n,fov=fov,obstacle=o,scene_id=s['scene_id'],**analyze(s)))
    cases=[c for r in rows for c in r['cases']]
    feasible=[c for c in cases if c['full_feasible']]
    summary=dict(base_scenes=len(rows),instances=len(cases),structurally_feasible=sum(r['min_full_time_s'] is not None for r in rows),budget_feasible=len(feasible),order_sensitive=sum(c['dead_end_fraction']>0 for c in feasible),minimum_views_hist=dict(Counter(str(r['minimum_views']) for r in rows)),by_fov={str(f):dict(mean_jaccard=fsum(r['mean_jaccard'] for r in rows if r['fov']==f)/32,structurally_feasible=sum(r['min_full_time_s'] is not None for r in rows if r['fov']==f)) for f in (18,55)},by_obstacle={str(o):dict(mean_blocked=fsum(r['blocked_edge_fraction'] for r in rows if r['obstacle']==o)/32) for o in (False,True)},by_ratio={str(b):dict(feasible=sum(c['full_feasible'] for c in cases if c['ratio']==b),order_sensitive=sum(c['dead_end_fraction']>0 for c in feasible if c['ratio']==b)) for b in RATIOS})
    Path('/mnt/data/rvi_r05_structural_audit.json').write_text(json.dumps(dict(summary=summary,rows=rows),indent=2)+'\n')
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
