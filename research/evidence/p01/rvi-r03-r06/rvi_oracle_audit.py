"""Independent retrospective audit of the known-geometry P01 artifact.

Exhaustive enumeration of distinct candidate sequences, using the recorded
simulator's straight-line, rotation, acquisition and visibility semantics.
No holdout scene bytes are read. No policy parameters are fitted.
"""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from math import atan2, fsum, hypot, pi, radians, remainder, ulp, isclose
from pathlib import Path
from zipfile import ZipFile


def angle(a, b):
    return abs(remainder(a-b, 2*pi))


def distance(p, a, b):
    dx, dy = b['x']-a['x'], b['y']-a['y']
    length = hypot(dx, dy)
    if not length:
        return hypot(p['x']-a['x'], p['y']-a['y'])
    ux, uy = dx/length, dy/length
    t = max(0., min(length, (p['x']-a['x'])*ux+(p['y']-a['y'])*uy))
    return hypot(p['x']-(a['x']+t*ux), p['y']-(a['y']+t*uy))


def blocked(scene, a, b, radius=0):
    return any(distance(o,a,b) <= o['radius_m']+radius+1e-10
               for o in scene['obstacles'])


def visible(scene, v):
    c = scene['camera']
    result = set()
    for p in scene['patches']:
        dx,dy = p['x']-v['x'],p['y']-v['y']
        d = hypot(dx,dy)
        if d == 0 or not c['min_range_m'] <= d <= c['max_range_m']:
            continue
        if angle(atan2(dy,dx),v['yaw_rad']) > c['horizontal_fov_rad']/2+1e-12:
            continue
        if angle(atan2(-dy,-dx),p['normal_rad']) > c['max_incidence_rad']+1e-12:
            continue
        if not blocked(scene,v,p):
            result.add(p['identifier'])
    return result


def transition(scene,a,b,t):
    m=scene['motion']; d=hypot(b['x']-a['x'],b['y']-a['y'])
    total=t+(d/m['linear_speed_m_s']+angle(b['yaw_rad'],a['yaw_rad'])/m['angular_speed_rad_s']+m['capture_duration_s'])
    if total > m['max_time_s'] and total-m['max_time_s'] > 8*max(ulp(total),ulp(m['max_time_s'])):
        return 'time_budget_exceeded',t,0
    if blocked(scene,a,b,m['robot_radius_m']):
        return 'path_collision',t,0
    return None,total,d


def oracle(scene):
    """Enumerate every feasible prefix, including zero-gain transit views."""
    route=scene['route']; n=len(route)
    if n>9:
        raise ValueError('exact enumeration restricted to at most 9 candidates')
    areas={p['identifier']:p['area_m2'] for p in scene['patches']}
    all_ids=set(areas); denominator=fsum(areas.values())
    views=[visible(scene,v) for v in route]
    best=(-1.,float('inf'),()); full=None; visited=0
    def walk(pos,t,coverage,used,seq):
        nonlocal best,full,visited
        visited+=1
        value=fsum(areas[k] for k in sorted(coverage))/denominator
        if (-value,t,seq)<(-best[0],best[1],best[2]):
            best=(value,t,seq)
        if coverage==all_ids:
            if full is None or (t,seq)<full:
                full=(t,seq)
            return
        for i,v in enumerate(route):
            if i in used: continue
            reason,newt,_=transition(scene,pos,v,t)
            if reason is None:
                walk(v,newt,coverage|views[i],used|{i},seq+(i+1,))
    walk(scene['start'],0.,set(),set(),())
    return dict(full_feasible=full is not None,optimal_coverage=best[0],
                optimal_elapsed_s=best[1],optimal_route=list(best[2]),
                full_min_time_s=None if full is None else full[0],prefixes=visited)


def replay(scene, trial):
    pos=scene['start']; t=d=0.; covered=set(); used=set()
    for event in trial['observations']:
        i=int(event['candidate_id'].split('_')[-1])-1
        assert i not in used
        used.add(i); v=scene['route'][i]
        assert v==event['requested_pose']
        reason,nt,nd=transition(scene,pos,v,t)
        assert reason==event['failure_reason']
        actual=set() if reason else visible(scene,v)
        assert actual==set(event['visible_patch_ids'])
        t=nt; d+=nd; covered|=actual
        if not reason: pos=v
        assert pos==event['pose']
        assert isclose(t,event['elapsed_time_s'],abs_tol=1e-12)
        assert isclose(d,event['travel_distance_m'],abs_tol=1e-12)
    assert covered==set(trial['covered_patch_ids'])
    assert isclose(t,trial['elapsed_time_s'],abs_tol=1e-12)
    assert isclose(d,trial['travel_distance_m'],abs_tol=1e-12)
    areas={p['identifier']:p['area_m2'] for p in scene['patches']}
    assert isclose(fsum(areas[k] for k in covered)/fsum(areas.values()),trial['sampled_surface_coverage'],abs_tol=1e-12)
    assert (covered==set(areas))==(trial['status']=='completed')
    return len(trial['observations'])


def audit(path):
    rows=[]; checks=0; replay_events=0
    with ZipFile(path) as z:
        names=z.namelist()
        assert len(names)==len(set(names))
        assert not any('/scenes/holdout/' in n or '/scenes/development/' in n or '/suites/holdout/' in n or '/suites/development/' in n for n in names)
        for line in z.read('SHA256SUMS').decode().splitlines():
            digest,name=line.split(maxsplit=1); name=name.removeprefix('./')
            assert sha256(z.read(name)).hexdigest()==digest
            checks+=1
        mraw=z.read('population/manifest.json'); m=json.loads(mraw)
        r=json.loads(z.read('calibration.json'))
        assert sha256(mraw).hexdigest()==r['manifest_sha256']
        records={x['scene_id']:x for x in m['scenes'] if x['partition']=='pilot' and '__i_reference__' in x['cell_id']}
        scenes={}
        for key,record in records.items():
            assert record['path'].startswith('scenes/pilot/') and '..' not in Path(record['path']).parts
            raw=z.read('population/'+record['path']); assert sha256(raw).hexdigest()==record['sha256']
            scenes[key]=json.loads(raw)
        def case(pop,scene,trials,meta):
            nonlocal replay_events
            assert len(trials)==5 and len({t['method'] for t in trials})==5
            result=oracle(scene)
            for t in trials:
                replay_events+=replay(scene,t)
                success=t['status']=='completed'; gap=result['optimal_coverage']-t['sampled_surface_coverage']
                assert not success or result['full_feasible']; assert gap>=-1e-12
                rows.append(dict(population=pop,scene_id=t['scene_id'],method=t['method'],success=success,
                                 failure_reason=t['failure_reason'],coverage=t['sampled_surface_coverage'],
                                 gap=max(0.,gap),classification='success' if success else 'avoidable' if result['full_feasible'] else 'infeasible',**meta,**result))
        for cfg in r['configurations']:
            groups=defaultdict(list)
            for t in cfg['trials']: groups[t['scene_id']].append(t)
            assert set(groups)==set(scenes)
            for key,trials in groups.items():
                assert all(t['scene_sha256']==records[key]['sha256'] for t in trials)
                original=scenes[key]
                scene=dict(original,camera=dict(original['camera'],horizontal_fov_rad=radians(cfg['fov_deg'])),motion=dict(original['motion'],max_time_s=float(cfg['budget_s'])))
                case('factorial',scene,trials,dict(family=records[key]['family'],budget_s=cfg['budget_s'],fov_deg=cfg['fov_deg']))
        for family in r['tradeoff_population']['families']:
            for c in family['cases']:
                case('stress',c['scene'],c['trials'],dict(family=family['family'],budget_ratio=c['budget_ratio'],capture_ratio=c['capture_ratio'],order=c['order']))
        assert len(rows)==5280
        source=z.read('source-sha.txt').decode().strip()
    def summary(group):
        classes=Counter(x['classification'] for x in group)
        failures=classes['avoidable']+classes['infeasible']
        return dict(trials=len(group),success=classes['success'],failures=failures,avoidable=classes['avoidable'],infeasible=classes['infeasible'],feasible=classes['success']+classes['avoidable'],mean_gap=fsum(x['gap'] for x in group)/len(group),positive_gap=sum(x['gap']>1e-12 for x in group),avoidable_failure_rate=classes['avoidable']/(classes['success']+classes['avoidable']) if classes['success']+classes['avoidable'] else None,avoidable_share_of_failures=classes['avoidable']/failures if failures else None)
    summaries={}
    for pop in ('factorial','stress'):
        g=[x for x in rows if x['population']==pop]; summaries[pop]={'all':summary(g),'methods':{method:summary([x for x in g if x['method']==method]) for method in sorted({x['method'] for x in g})},'instances':len(g)//5,'feasible_instances':sum(x['full_feasible'] for x in g)//5,'max_prefixes':max(x['prefixes'] for x in g)}
    return dict(stage='exploratory_not_confirmatory',source_sha=source,archive_sha256=sha256(Path(path).read_bytes()).hexdigest(),checksums=checks,replayed_events=replay_events,summaries=summaries,rows=rows)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('artifact');p.add_argument('output');a=p.parse_args()
    result=audit(a.artifact)
    Path(a.output).write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
