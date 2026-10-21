#!/usr/bin/env python3
"""Check saved STEP geometry against explicit task dimensions, independently of JSON parameters."""
import hashlib, json, math
from pathlib import Path
import cadquery as cq

ROOT=Path(__file__).resolve().parent
CHECKS=[]

def solid(group,key):return cq.importers.importStep(str(ROOT/'models'/group/(key.replace('.','p')+'.step'))).val()
def check(name,actual,expected,tol=.02):
    ok=abs(actual-expected)<=tol
    CHECKS.append(dict(check=name,measured=actual,expected=expected,tolerance=tol,passed=ok))
def truth(name,passed):CHECKS.append(dict(check=name,passed=bool(passed)))
def ext(s):
    b=s.BoundingBox();return [b.xlen,b.ylen,b.zlen]
def inside(s,x,y,z):return s.isInside(cq.Vector(x,y,z),1e-5)

def main():
    for thickness in [3,2,1,.8]:
        card=solid('B32',f'card_t{thickness:g}')
        for axis,value in enumerate([85,54,thickness]):check(f'card_{thickness}_size_{axis}',ext(card)[axis],value)
        truth(f'card_{thickness}_rounded_corner',not inside(card,42.49,26.99,thickness/2) and inside(card,0,0,thickness/2))
        # Insert the exact exported card into its corresponding exported slot.
        placed=card.rotate((0,0,0),(1,0,0),90).translate(cq.Vector(0,thickness/2,36))
        holder=solid('B33',f'card_slot_t{thickness:g}')
        check(f'card_{thickness}_slot_interference_mm3',holder.intersect(placed).Volume(),0,.001)
    tube=solid('B25','printed_tube_12x75')
    for axis,value in enumerate([12,12,75]):check(f'printed_tube_size_{axis}',ext(tube)[axis],value)
    truth('tube_open_top_closed_bottom',not inside(tube,0,0,74) and inside(tube,0,0,1))
    truth('tube_hollow_wall',not inside(tube,4.35,0,30) and inside(tube,4.45,0,30))
    for diameter in [16,15,14,13.5]:
        guide=solid('P05',f'rack_guide_{diameter:g}').rotate((0,0,0),(1,0,0),180).translate(cq.Vector(0,0,80))
        for x in [-34.5,-11.5,11.5,34.5]:
            placed=tube.translate(cq.Vector(x,0,18))
            check(f'tube_in_rack_{diameter}_{x}_interference_mm3',guide.intersect(placed).Volume(),0,.001)
    for kind in ['round','square']:
        for diameter in [28,24,22,21]:
            s=solid('P01',f'{kind}_base_{diameter}')
            for i,value in enumerate([100,100,30]):check(f'{kind}_{diameter}_bbox_{i}',ext(s)[i],value)
            for z in [1,10,25,28.5]:
                truth(f'{kind}_{diameter}_bore_at_{z}',not inside(s,diameter/2-.03,0,z) and inside(s,diameter/2+.03,0,z))
            truth(f'{kind}_{diameter}_chamfer',inside(s,diameter/2+.5,0,29.25) and not inside(s,diameter/2+.5,0,29.75))
    for h in [60,80]:
        s=solid('P01',f'round_peg_{h}');check(f'peg_{h}_length',ext(s)[2],h)
        truth(f'peg_{h}_shaft_20',inside(s,9.98,0,15) and not inside(s,10.02,0,15))
    for d in [16,15,14,13.5]:
        s=solid('P05',f'rack_guide_{d:g}')
        check(f'rack_{d}_assembled_height',ext(s)[2]+ext(solid('P05','rack_weight_base'))[2]+ext(solid('P05','rack_weight_lid'))[2],80)
        # Guide was inverted for printing; entry at z=0, bore runs upward 45 mm.
        for x in [-34.5,-11.5,11.5,34.5]:
            truth(f'rack_{d}_guide_{x}',not inside(s,x+d/2-.03,0,30) and inside(s,x+d/2+.03,0,30))
            truth(f'rack_{d}_depth_{x}',inside(s,x+d/2+.5,0,44.9) and not inside(s,x+d/2+.5,0,45.1))
    cup=solid('P03','weighted_cup')
    for i,value in enumerate([70,70,90]):check(f'cup_bbox_{i}',ext(cup)[i],value)
    body=solid('P07','weight_box_body');lid=solid('P07','weight_box_lid')
    for i,value in enumerate([100,60]):check(f'weight_box_bbox_{i}',ext(body)[i],value)
    check('weight_box_assembled_height',ext(body)[2]+ext(lid)[2],40)
    for count in [2,3,4,5]:
        s=solid('P07',f'tray_{count}_balls');pts=[]
        for face in s.Faces():
            if face.geomType()=='SPHERE':
                b=face.BoundingBox();pts.append(((b.xmin+b.xmax)/2,(b.ymin+b.ymax)/2))
        check(f'tray_{count}_seat_count',len(pts),count,0)
        nearest=[min(math.dist(a,b) for j,b in enumerate(pts) if i!=j) for i,a in enumerate(pts)]
        for i,value in enumerate(nearest):check(f'tray_{count}_nearest_pitch_{i}',value,50)
    for d in [50,80]:
        s=solid('P08',f'knob_{d}');check(f'knob_{d}_diameter_x',ext(s)[0],d);check(f'knob_{d}_diameter_y',ext(s)[1],d)
    check('cabinet_roof_width',ext(solid('P02','cabinet_roof'))[0],250)
    check('cabinet_roof_depth',ext(solid('P02','cabinet_roof'))[1],300)
    check('cabinet_body_height_with_roof',ext(solid('P02','cabinet_shell'))[2]+ext(solid('P02','cabinet_roof'))[2],150)
    handle=solid('P02','drawer_handle')
    # Centre section is a round bar; bottom of its occupied interval is exactly net gap.
    truth('handle_net_gap_42',not inside(handle,0,0,41.98) and inside(handle,0,0,42.02))
    result=dict(source='exported STEP geometry; v0.3.3 dimensions with user-approved printed cards and tubes; purchased bottle excluded',manifest_sha256=hashlib.sha256((ROOT/'manifest.json').read_bytes()).hexdigest(),checks=CHECKS,passed=sum(c['passed'] for c in CHECKS),total=len(CHECKS),physical_fit_verified=False)
    (ROOT/'geometry_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps(dict(passed=result['passed'],total=result['total'],failed=[c for c in CHECKS if not c['passed']]),ensure_ascii=False))
    if result['passed']!=result['total']:raise SystemExit(1)

if __name__=='__main__':main()
