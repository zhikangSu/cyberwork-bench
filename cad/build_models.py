#!/usr/bin/env python3
"""Editable, millimetre-native CadQuery prototypes. No hardware or simulator writes.

Run with ../../.venv-cad/bin/python build_models.py from this directory.
Shapes are exported as single printable parts, not overlapping display primitives.
"""
from __future__ import annotations
import argparse, hashlib, json, math, time
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent
P = json.loads((ROOT / 'parameters.json').read_text())
OUT = ROOT / 'models'
M = P['manufacturing']
PARTS = []
CHECKS = []
GROUPS = {
 'B32': ('打印卡片', 'H3', '用户调整 · 待试印', '85×54 mm，厚度 3 / 2 / 1 / 0.8 mm，四档配对应卡槽。按用户要求改为塑料打印，材质、摩擦和厚度需实测。'),
 'B25': ('打印试管', 'D3 / D7', '用户调整 · 待试印', '外径 12 mm、总长 75 mm，开口空心管，封底；与四档试管架及 V 托配套打印。打印后核对外径和夹持刚度。'),
 'B33': ('卡槽', 'H3', '尺寸原型', '四档卡槽与打印卡片配套；槽间隙是设计参数，首件需实测试插。'),
 'P01': ('销与孔座', 'S2', '尺寸原型', '含圆孔四档、方孔四档及长销；H2S 打印后必须量孔与修孔，L3/L4 未经实测不得用于正式精度评测。'),
 'P02': ('抽屉柜与分度转台', 'S3 / S7 / S11', '接口待测', '柜体与抽屉尺寸已建；滑轨按单侧厚 12.7 mm 假设，采购后核实厚度、孔位、200 mm 行程及 2 N 拉力。'),
 'P03': ('配重杯', 'S4 / H9', '尺寸原型', '70×90 mm 杯体，底部配重腔与螺钉盖。配重及打印支撑清理后称重。'),
 'P04': ('薄口簸箕', 'S5', '尺寸原型', '150 mm 净开口，0.4 mm 入口，斜坡约 4.6°，后侧磁铁座。'),
 'P05': ('试管架与 V 形管托', 'D3 / D7', '尺寸原型', '四档孔径及 45 mm 导向孔；总高 80 mm。独立配重底座与导向架以 M3 螺钉连接，装配后配重到 150 g 并贴毛毡。'),
 'P07': ('球托、浅槽托盘与配重盒', 'H1 / H5 / H6', '尺寸原型', '球托四档、2/3/4/5 球布局，邻近球心距 50 mm；配重盒外形 100×60×40 mm，装好后称到 150 g。'),
 'P08': ('旋钮台', 'H4', '接口待测', '50 / 80 mm 旋钮、双 608 轴承座、摩擦制动座及电位器架；轴承、8 mm 轴、O 形圈、电位器外购。阻力矩必须实测标定。'),
 'P09': ('四键键盘', 'H6', '接口待测', '四个名义 30 mm 安装孔，55 mm 中心距；按钮外沿直径须 ≤35 mm 才能保持 ≥20 mm 净距。实际按钮型号待选。'),
 'P10': ('喷壶改装件与靶板架', 'H2 / H-open', '接口待测', '喷壶颈 25 mm、激光模块 8 mm 均为可调假设；微动开关与电子器件外购。A4 靶板不预设任务命中区域大小。'),
 'P12': ('纸箱复位与底角夹具', 'H7', '尺寸原型', '90° 角尺仅供复位，开始任务前撤走；底角固定件不接触翻盖，不替代纸箱自互锁。'),
 'P13': ('相机支架与法兰测量毛坯', '共用工位', '接口待测', '相机板为通用长孔草模；手—RM75-B 转接件是无孔位毛坯，必须实测两端接口再补孔，不可直接安装承载。R5 即 L5 Pro。'),
}

def box(x,y,z,at=(0,0,0)):
    return cq.Workplane('XY').box(x,y,z,centered=(True,True,False)).translate(at)

def cyl(r,h,at=(0,0,0)):
    return cq.Workplane('XY').circle(r).extrude(h).translate(at)

def cone(r0,r1,h,at=(0,0,0)):
    return cq.Workplane(obj=cq.Solid.makeCone(r0,r1,h)).translate(at)

def bore(s,d,h,at=(0,0,0)):
    return s.cut(cyl(d/2,h,at))

def holes(s,points,d,z,h):
    for x,y in points: s=bore(s,d,h,(x,y,z))
    return s

def magnets(s,points):
    return holes(s,points,M['magnet_d'],-0.01,M['magnet_depth']+0.01)

def slot(length,width,h,at=(0,0,0),angle=0):
    return cq.Workplane('XY').slot2D(length,width,angle).extrude(h).translate(at)

def chamfer_hole(s,d,depth,x=0,y=0,top=None):
    if top is None: top=depth
    s=bore(s,d,depth+0.02,(x,y,top-depth-0.01))
    return s.cut(cone(d/2,d/2+1,1,(x,y,top-1)))

def shell(x,y,h,w=3,floor=3):
    return box(x,y,h).cut(box(x-2*w,y-2*w,h,(0,0,floor)))

def enclosure(x,y,h,w=3,lid=3):
    points=[(sx*(x/2-w-4),sy*(y/2-w-4)) for sx in [-1,1] for sy in [-1,1]]
    body=shell(x,y,h-lid,w,w)
    for x0,y0 in points:body=body.union(cyl(4.6,h-lid,(x0,y0,0)))
    body=holes(body,points,M['m3_pilot'],h-lid-12,13)
    cover=holes(box(x,y,lid),points,M['m3_clearance'],-0.1,lid+0.2)
    return body,cover,points

def emit(group,key,name,s,qty=1,variant='BASE',note='',orientation=None,placement=None):
    """Export current shape in a documented print orientation, bed at z=0."""
    key=key.replace('.', 'p')
    if orientation:s=s.rotate((0,0,0),orientation[0],orientation[1])
    bb=s.val().BoundingBox(); s=s.translate((-(bb.xmin+bb.xmax)/2,-(bb.ymin+bb.ymax)/2,-bb.zmin))
    shape=s.val(); solids=shape.Solids()
    if len(solids)!=1 or not shape.isValid():raise ValueError(f'{key}: invalid / {len(solids)} solids')
    target=OUT/group;target.mkdir(parents=True,exist_ok=True)
    path=target/key
    cq.exporters.export(s,str(path.with_suffix('.step')))
    cq.exporters.export(s,str(path.with_suffix('.stl')),tolerance=0.06,angularTolerance=0.15)
    mesh=trimesh.load_mesh(path.with_suffix('.stl'),process=True)
    keep=mesh.nondegenerate_faces()
    removed=int(len(keep)-np.count_nonzero(keep))
    if removed:
        # OCC may emit zero-area triangles at spherical poles. Remove only those;
        # do not fill holes, smooth, scale or otherwise repair the designed surface.
        mesh.update_faces(keep);mesh.remove_unreferenced_vertices()
        mesh.export(path.with_suffix('.stl'))
    dims=np.array(mesh.extents); build=np.array(P['printer']['build_mm']); margin=P['printer']['edge_margin_mm']
    fits=bool(dims[0]<=build[0]-2*margin and dims[1]<=build[1]-2*margin and dims[2]<=build[2])
    fits90=bool(dims[1]<=build[0]-2*margin and dims[0]<=build[1]-2*margin and dims[2]<=build[2])
    validation=dict(occ_valid=shape.isValid(),solid_count=len(solids),watertight=bool(mesh.is_watertight),winding_consistent=bool(mesh.is_winding_consistent),positive_volume=bool(mesh.volume>0),h2s_fits_with_5mm_margin=fits or fits90,bed_rotation_deg=0 if fits else 90,zero_area_triangles_removed=removed)
    if not all(validation[k] for k in ['occ_valid','watertight','winding_consistent','positive_volume','h2s_fits_with_5mm_margin']):raise ValueError(f'{key}: {validation}')
    row=dict(group=group,id=key,name=name,quantity=qty,variant=variant,notes=note,dimensions_mm=np.round(dims,3).tolist(),solid_volume_cm3=round(shape.Volume()/1000,3),files={ext:str(path.with_suffix('.'+ext).relative_to(ROOT)) for ext in ['stl','step']},validation=validation,sha256=hashlib.sha256(path.with_suffix('.stl').read_bytes()).hexdigest(),placement=placement,print_origin_mm=[(bb.xmin+bb.xmax)/2,(bb.ymin+bb.ymax)/2,bb.zmin],print_rotation=orientation)
    PARTS.append(row)
    print(f'{group} {key}: {np.round(dims,1).tolist()} valid',flush=True)
    return s

def build_printed_cards():
    p=P['card']
    for thickness in p['thicknesses']:
        card=box(p['length'],p['width'],thickness).edges('|Z').fillet(p['corner_radius'])
        emit('B32',f'card_t{thickness:g}',f'配套卡片 · {thickness:g} mm',card,qty=3,variant='BASE' if thickness==2 else '阶梯',note=f'85×54×{thickness:g} mm，圆角 R{p["corner_radius"]} 为设计值；平放打印，保持表面平整，不做凸字。配 card_slot_t{thickness:g}。材质改为打印塑料，厚度和摩擦需实测。')

def build_printed_tube():
    p=P['tube']
    outer=cyl(p['outer_d']/2,p['length']).edges('<Z').fillet(p['bottom_edge_radius'])
    tube=outer.cut(cyl(p['outer_d']/2-p['wall'],p['length'],(0,0,p['bottom'])))
    emit('B25','printed_tube_12x75','配套空心试管 · Ø12×75 mm',tube,qty=2,note='外径 12、总长 75；上端开口，底厚 2、壁厚 1.6 mm，底边 R1.2 为设计值。竖直打印，切片检查附着；距底 30 mm 画色带，不做凸环。打印后量外径、长和夹持刚度。')

def build_card():
    for t in P['card']['thicknesses']:
        gap=t+P['card']['slot_clearance']
        s=box(120,60,6).union(box(100,20,30,(0,0,6)))
        s=s.cut(box(90,gap,30,(0,0,9)))
        s=holes(s,[(-48,-22),(48,22)],4.5,-.1,7)
        emit('B33',f'card_slot_t{t:g}','卡槽：卡厚 '+str(t)+' mm',s,variant='BASE' if t==2 else '阶梯',note=f'槽宽 {gap:g} mm；槽深 27 mm；配同档打印卡片，卡片与卡槽一起试印。')

def build_pegs():
    q=P['peg'];x,y,h=q['base']
    for square in [False,True]:
        for d in q['holes']:
            s=box(x,y,h)
            if square:
                s=s.cut(box(d,d,h+2,(0,0,-1)))
                lead=cq.Workplane('XY').workplane(offset=h-1).rect(d,d).workplane(offset=1).rect(d+2,d+2).loft()
                s=s.cut(lead)
            else:s=chamfer_hole(s,d,h)
            s=magnets(s,[(a,b) for a in [-35,35] for b in [-35,35]])
            emit('P01',f'{"square" if square else "round"}_base_{d}','方孔底座' if square else '圆孔底座',s,qty=2,variant='BASE' if d==24 and not square else 'OOD' if square else '阶梯',note=f'通孔 {d} mm，入口 1×45°；桌面作为孔底。4 颗 Ø10×3 mm 磁铁需购买。')
    for length in q['lengths']:
        s=cyl(q['diameter']/2,length-6).union(cq.Workplane('XY').polygon(6,30).extrude(6).translate((0,0,length-6)))
        emit('P01',f'round_peg_{length}','六角法兰圆销',s,qty=4 if length==60 else 2,variant='BASE' if length==60 else 'OOD',note='以底端为零，在 5、25 mm 处画色带；销身不增加凸环。')
    emit('P01','square_peg_60','方销',box(20,20,54).union(box(28,28,6,(0,0,54))),variant='OOD',note='方截面 20×20；总长 60。')
    # Matching test only; coupon thickness is not the benchmark hole depth.
    s=box(125,36,8)
    for i,d in enumerate(q['holes']):s=chamfer_hole(s,d,8,x=(i-1.5)*29)
    emit('P01','peg_fit_coupon','孔径试印片',s,variant='试样',note='只用于打印尺寸检查，不替代 30 mm 深任务底座。')

def build_drawer():
    p=P['drawer'];w,d,h=p['cabinet'];t=p['wall']
    # Front at negative Y. Roof removable. Through slots allow purchased rail adjustment.
    c=box(w,d,t).union(box(t,d,h-t,(-w/2+t/2,0,0))).union(box(t,d,h-t,(w/2-t/2,0,0))).union(box(w,t,h-t,(0,d/2-t/2,0)))
    for z in [38,68]:
        for y in [-90,0,90]:
            cut=slot(45,4.5,w+2,angle=90).rotate((0,0,0),(0,1,0),90).translate((-w/2-1,y,z))
            c=c.cut(cut)
    roofpts=[(a,b) for a in [-w/2+9,w/2-9] for b in [-d/2+18,d/2-18]]
    for a,b in roofpts:c=c.union(cyl(6,18,(a,b,h-t-18)))
    c=holes(c,roofpts,2.5,h-20,22)
    # Positive cabinet-to-rotor screw locations.
    mount=[(a,b) for a in [-70,70] for b in [-65,65]]
    c=holes(c,mount,4.5,-.1,t+.2)
    emit('P02','cabinet_shell','柜体开顶壳',c,note='开口朝前；顶部装独立盖板。侧壁长孔为通用滑轨调节孔，购买滑轨后复核。')
    lid=holes(box(w,d,t),roofpts,3.4,-.1,t+.2)
    emit('P02','cabinet_roof','柜体顶板',lid,note='4 个 M3 自攻或塑料螺纹螺钉；拧紧前实测。')
    dw=w-2*t-2*(p['rail_thickness_assumed']+p['rail_side_clearance'])
    tub=shell(dw,p['drawer_depth'],p['drawer_height'],t,t)
    # Rail slots on both drawer sides, plus through front handle mounting holes.
    for z in [32,62]:
        for y in [-70,0,70]:tub=tub.cut(slot(35,4.5,dw+2,angle=90).rotate((0,0,0),(0,1,0),90).translate((-dw/2-1,y,z)))
    for x in [-60,60]:tub=tub.cut(cyl(2.25,t+2).rotate((0,0,0),(1,0,0),90).translate((x,-p['drawer_depth']/2+t+1,65)))
    emit('P02','drawer_tub','抽屉',tub,note=f'外宽 {dw:g} mm；内高 {p["drawer_height"]-t:g} mm；只含塑料箱体，滑轨外购。')
    # Handle printed with mounting faces on bed; crossbar bridges need slicer support.
    span=p['handle_span'];r=p['handle_d']/2;zc=p['handle_net_gap']+r
    handle=cyl(r,span+2*r).rotate((0,0,0),(0,1,0),90).translate((-span/2-r,0,zc))
    for x in [-span/2,span/2]:handle=handle.union(cyl(9,zc,(x,0,0))).union(cyl(13,5,(x,0,0)))
    handle=holes(handle,[(-span/2,0),(span/2,0)],3.3,-.1,20)
    emit('P02','drawer_handle','Ø20 横杆把手',handle,note=f'横杆至安装面净空 {p["handle_net_gap"]} mm，M4 螺钉底装。横杆悬空需支撑。')
    rad=p['index_radius'];base=cyl(150,8).union(box(180,50,8,(0,-144,0)));rotor=cyl(125,8)
    # Index arm reaches outside the circular support; cabinet's front edge is Y=-150.
    rotor=rotor.union(box(20,rad-100,8,(0,-(rad+120)/2,0)))
    rotor=holes(rotor,mount,4.5,-.1,9)
    for angle in p['index_angles']:
        a=math.radians(angle);base=bore(base,5.3,10,(rad*math.sin(a),-rad*math.cos(a),-1))
    base=bore(base,8.5,10,(0,0,-1));rotor=bore(rotor,8.5,10,(0,0,-1));rotor=bore(rotor,5.3,10,(0,-rad,-1))
    for x in [-95,95]:base=base.cut(slot(30,6.5,10,(x,95,-1)))
    emit('P02','index_base','分度底盘',base,orientation=((0,0,1),90),note='M8 中心轴，M5 定位销；0/±10/±20/±30° 孔。底盘已转 90° 适配 H2S 平台，装配时复原方向并与桌面夹紧。')
    emit('P02','index_rotor','柜底转盘与分度臂',rotor,note='4 个 M4 螺栓连接柜底；分度臂在柜体下方，先拔销再转动。加薄垫片消除盘间摩擦。')

def build_cup():
    p=P['cup'];r=p['diameter']/2
    body=cyl(r,p['height']).cut(cyl(r-p['wall'],p['height'],(0,0,12)))
    body=body.cut(cyl(p['ballast_d']/2,p['ballast_height']+2,(0,0,-.1))).cut(cyl(29,2,(0,0,-.01)))
    pts=[(26*math.cos(a*math.pi/2),26*math.sin(a*math.pi/2)) for a in range(4)]
    body=holes(body,pts,2.5,1.9,8)
    cap=holes(cyl(28.8,2),pts,3.4,-.1,2.2)
    emit('P03','weighted_cup','配重杯体',body,note='底部配重腔朝下；腔顶需支撑，支撑从底部开口取出。4×M3 螺钉固定底盖。')
    emit('P03','cup_ballast_lid','杯底配重盖',cap,note='腔体内填固定的配重；不要让金属块自由晃动。')

def build_dustpan():
    p=P['dustpan'];w=p['opening'];d=p['depth'];t=p['wall'];f=p['floor'];run=p['ramp_run']
    s=box(w+2*t,d,f).union(box(t,d,32,(-w/2-t/2,0,0))).union(box(t,d,32,(w/2+t/2,0,0))).union(box(w+2*t,t,32,(0,d/2-t/2,0)))
    ramp=cq.Workplane('YZ').polyline([(-d/2-run,0),(-d/2,0),(-d/2,f),(-d/2-run,p['toe'])]).close().extrude(w/2,both=True)
    s=s.union(ramp)
    for x in [-55,55]:s=s.union(box(18,18,6,(x,d/2+6,0)))
    s=magnets(s,[(x,d/2+6) for x in [-55,55]])
    emit('P04','dustpan','薄口磁吸簸箕',s,qty=2,note='开口净宽 150；薄边易翘曲，试印后放在实际桌垫上检查贴合。')

def build_racks():
    p=P['rack'];x,y,z=p['outer'];pts=[((i-1.5)*p['pitch'],0) for i in range(4)]
    mount=[(-43,-23),(-43,23),(43,-23),(43,23)]
    # Split bottom plate from tall guides: no sealed ballast pocket or inaccessible support.
    base=shell(x,y,15,3,3)
    base=base.union(box(90,6,15))
    for a,b in mount:base=base.union(cyl(4.5,15,(a,b,0)))
    base=holes(base,mount,2.5,4,12)
    emit('P05','rack_weight_base','试管架配重底座',base,qty=2,note='两侧开放腔放配重，装上导向架后封住；毛毡脚垫另贴，不固定到桌上。')
    emit('P05','rack_weight_lid','试管架配重盖板',holes(box(x,y,3),mount,3.4,-.1,3.2),qty=2,note='放在 15 mm 底座上，四根长螺钉穿过导向架和盖板进入底座。')
    for d in p['holes']:
        # Coordinates local: seated on 15-mm base plus 3-mm lid, upside-down to print.
        gh=z-18
        s=box(x,y,5,(0,0,gh-5))
        for a,b in mount:s=s.union(box(8,8,gh,(a,b,0)))
        for a,b in pts:
            s=s.union(cyl(d/2+2.5,p['guide_depth'],(a,b,gh-p['guide_depth'])))
            s=chamfer_hole(s,d,p['guide_depth'],a,b,gh)
        s=holes(s,mount,3.4,-.1,z)
        # Separate fastener tunnel accepts long M3 x 80 screws through top into base.
        emit('P05',f'rack_guide_{d:g}','四孔试管导向架',s,qty=2,variant='BASE' if d==15 else '阶梯',orientation=((1,0,0),180),note=f'孔 Ø{d:g}，孔口 1×45°。与底座及盖板组合总高 80。导向架倒置打印，顶板贴平台；4 根 M3×75 螺钉。')
    v=box(10,32,40)
    cutter=cq.Workplane('YZ').polyline([(-14,41),(0,27),(14,41)]).close().extrude(6,both=True)
    emit('P05','tube_v_rest','V 形管托',v.cut(cutter),qty=2,note='两只薄管托沿管长分开摆放，中间留给夹爪。')

def build_balls():
    p=P['balls']
    for d in p['diameters']:
        ri=d*.2;h=p['seat_height']
        s=cyl(ri+8,h).cut(cyl(ri,h+2,(0,0,-1))).cut(cone(ri,ri+3,3,(0,0,h-3)))
        emit('P07',f'ball_ring_{d}','低矮球托',s,variant='BASE' if d==110 else '阶梯',note=f'用于约 Ø{d} 球；实际球径与软硬程度需试摆。')
    pitch=p['pitch'];layouts={2:[(-25,0),(25,0)],3:[(-25,-pitch*math.sqrt(3)/6),(25,-pitch*math.sqrt(3)/6),(0,pitch*math.sqrt(3)/3)],4:[(-25,-25),(-25,25),(25,-25),(25,25)],5:[(0,0),(-50,0),(50,0),(0,-50),(0,50)]}
    x,y,z=p['tray'];pts=[(a,b) for a in [-85,85] for b in [-75,75]]
    for n,layout in layouts.items():
        s=holes(box(x,y,5),pts,3.4,-.1,5.2)
        for a,b in layout:
            sphere=cq.Workplane('XY').sphere(p['pingpong_d']/2+.2).translate((a,b,5+p['pingpong_d']/2+.2-p['pocket_depth']))
            s=s.cut(sphere)
        emit('P07',f'tray_{n}_balls',f'{n} 球浅槽托盘',s,variant='BASE' if n==3 else '阶梯',note='单独平放打印。4 只 40 mm 脚柱由上方 M3 螺钉连接；装好总高 45 mm。')
    foot=bore(cyl(10,40),2.5,16,(0,0,25))
    emit('P07','tray_foot','托盘脚柱',foot,qty=4,note='M3×12 螺钉；同一套脚可换不同球数托盘。')
    p=P['weight_box'];x,y,z=p['outer'];body,lid,_=enclosure(x,y,z,p['wall'],p['lid'])
    body=body.union(box(3,y-6,z-6,(0,0,3)))
    emit('P07','weight_box_body','150 g 配重盒主体',body,qty=2,note='添加固定的配重，装盖后称总质量 150 g。')
    emit('P07','weight_box_lid','配重盒平盖',lid,qty=2,note='4×M3×10；盖板装好外高 40 mm。')

def build_knob():
    p=P['knob'];r=p['shaft_d']/2
    for d in p['diameters']:
        s=cyl(d/2,p['length']).cut(cyl(r+.15,p['length']+2,(0,0,-1)))
        screw=cyl(1.65,d/2+1).rotate((0,0,0),(0,1,0),90).translate((0,0,8))
        emit('P08',f'knob_{d}','光滑圆旋钮',s.cut(screw),variant='BASE' if d==50 else 'OOD',note='M4 紧定螺钉不得凸出外圆；8 mm 轴的平面或防滑位置需实测。')
    # Horizontal shaft along Y, mounted 75 mm above a broad base.
    s=box(120,90,8).union(box(90,14,95,(0,0,8)))
    for x in [-48,48]:s=s.union(box(8,45,50,(x,8,8)))
    bearing_axis=cyl(p['bearing_od']/2+.1,7.2).rotate((0,0,0),(1,0,0),90)
    s=s.cut(bearing_axis.translate((0,7.1,75))).cut(bearing_axis.translate((0,.1,75)))
    s=s.cut(cyl(r+.3,25).rotate((0,0,0),(1,0,0),90).translate((0,12,75)))
    for x in [-16,16]:
        for z in [59,91]:s=s.cut(cyl(1.7,16).rotate((0,0,0),(1,0,0),90).translate((x,8,z)))
    s=magnets(s,[(a,b) for a in [-45,45] for b in [-30,30]])
    # Rear attachments have matched clearance holes in base, not arbitrary floating mounts.
    s=holes(s,[(-25,32),(25,32)],4.5,-.1,9)
    emit('P08','knob_bearing_stand','旋钮双轴承支座',s,note='2 个 608 轴承背靠背放入；前后盖板约束轴向位置，4×M3 贯穿螺栓。轴线高 75，实测轴承孔配合。底部 4 颗磁铁。')
    retain=bore(box(40,40,3),18,5,(0,0,-1))
    retain=holes(retain,[(x,y) for x in [-16,16] for y in [-16,16]],3.4,-.1,4)
    emit('P08','bearing_retainer','轴承外圈限位盖',retain,qty=2,note='4×M3×25 螺栓贯穿前盖、支架和后盖并用螺母固定；中央 Ø18 避开轴与内圈。需实测盖板与轴承外圈的间隙。')
    brake=box(42,24,38).cut(cyl(6,26).rotate((0,0,0),(1,0,0),90).translate((0,13,22)))
    brake=brake.cut(cyl(2.25,24,(0,0,18)))
    brake=brake.cut(box(9.4,8.4,12,(0,0,24)))
    brake=brake.union(box(64,24,5))
    brake=holes(brake,[(-25,0),(25,0)],4.5,-.1,6)
    emit('P08','friction_brake_block','O 形圈摩擦刹车块',brake,note='12 mm 腔容纳 8 mm 轴和 O 形圈；顶部 M4 螺钉压滑块，需加外置 M4 螺母。装在另设可调高支架上，按扭力计调到 0.1/0.2/0.3/0.4 N·m。')
    shoe=box(9,8,5).cut(cyl(4,10).rotate((0,0,0),(1,0,0),90).translate((0,5,-1)))
    emit('P08','brake_pressure_shoe','刹车压块',shoe,note='位于 M4 螺钉与 O 形圈之间，保护橡胶。')
    # Riser makes the brake's axis exactly match the 75-mm axis over 8-mm base.
    riser=holes(box(64,24,45),[(-25,0),(25,0)],4.5,-.1,46)
    emit('P08','brake_riser','刹车增高块',riser,note='底座 8 + 增高 45 + 刹车轴心 22 = 75 mm；2×M4 长螺栓。')
    pot=box(70,30,5).union(box(70,5,90,(0,12.5,0)))
    pot=pot.cut(slot(30,10,7,angle=90).rotate((0,0,0),(1,0,0),90).translate((0,16,70)))
    for x in [-25,25]:pot=pot.cut(slot(20,4.5,7,(x,0,-1),90))
    emit('P08','potentiometer_bracket','电位器调节架',pot,note='电位器螺纹安装段和本体待测；轴高可调。该架独立固定桌面，防止给电位器轴施加侧向载荷。')
    coupler=cyl(8,24).cut(cyl(r+.15,12.1,(0,0,-.1))).cut(cyl(p['pot_shaft_assumed']/2+.15,12.1,(0,0,12)))
    for z in [6,18]:coupler=coupler.cut(cyl(1.65,9).rotate((0,0,0),(0,1,0),90).translate((0,0,z)))
    emit('P08','shaft_coupler_8_6','8→6 mm 轴联轴套',coupler,note='6 mm 为电位器轴径假设；2×M4 紧定螺钉。')

def build_keypad():
    p=P['keypad'];x,y,z=p['outer'];body,lid,_=enclosure(x,y,z,3,4)
    body=body.cut(box(16,10,10,(0,y/2,12)))
    for i in range(4):lid=bore(lid,p['button_hole_assumed'],6,((i-1.5)*p['button_pitch'],0,-1))
    # Cable-tie slots for a generic removable Pro Micro carrier (PCB hole pattern unknown).
    pcb=box(55,30,3)
    for a in [-18,18]:pcb=pcb.cut(slot(18,3.5,5,(a,0,-1),90))
    emit('P09','keypad_body','四键键盘壳',body,note='4×M3 固定盖板；用桌面夹具固定键盘，线缆由后窗穿出。')
    emit('P09','keypad_top','四键键盘面板',lid,note='键帽贴 1–4，按实际按钮本体与卡扣长度修改安装孔。')
    emit('P09','keypad_pcb_carrier','USB 控制板绑扎座',pcb,note='Pro Micro 用扎带固定；底部胶贴固定到键盘壳内，避免假设 PCB 孔位。')

def split_clamp(inner,width=12):
    r=inner/2;outer=r+5
    s=cyl(outer,width).cut(cyl(r+.2,width+2,(0,0,-1)))
    s=s.union(box(2*outer+14,10,width)).cut(cyl(r+.2,width+2,(0,0,-1)))
    # Split on Y; one M3 clamp screw on each ear, axis Y.
    for x in [-outer-3,outer+3]:s=s.cut(cyl(1.7,12).rotate((0,0,0),(1,0,0),90).translate((x,6,width/2)))
    return s.intersect(box(2*outer+30,outer+10,width,(0,(outer+10)/2+.25,0))),s.intersect(box(2*outer+30,outer+10,width,(0,-(outer+10)/2-.25,0)))

def build_spray():
    p=P['spray']
    a,b=split_clamp(p['bottle_neck_assumed'])
    # Flat fastening tab on one half for the adjustable switch and laser brackets.
    tab=box(20,18,4,(0,p['bottle_neck_assumed']/2+10,0))
    tab=holes(tab,[(-5,p['bottle_neck_assumed']/2+13),(5,p['bottle_neck_assumed']/2+13)],3.4,-.1,5)
    emit('P10','spray_neck_front','喷壶颈前夹环',a.union(tab),note='默认 Ø25 颈；测量喷壶后修改。前后夹环以 2 根 M3 螺钉连接，夹缝不应完全压死。')
    emit('P10','spray_neck_back','喷壶颈后夹环',b)
    s=box(40,22,4).union(box(40,4,35,(0,9,0)))
    for x in [-12,12]:s=s.cut(slot(15,3.4,6,(x,0,-1),90))
    for x in [-10,10]:s=s.cut(slot(22,2.5,6,angle=90).rotate((0,0,0),(1,0,0),90).translate((x,12,20)))
    emit('P10','trigger_switch_bracket','扳机微动开关长孔支架',s,note='开关触发行程与按钮孔距待选型，不应增加或绕过任务规定扳机阻力。')
    a,b=split_clamp(p['laser_d_assumed'],10)
    emit('P10','laser_front','激光模块前夹环',a,note='默认 Ø8 激光管；测量实际模块后调整。与支架螺栓/小型角片连接。')
    emit('P10','laser_back','激光模块后夹环',b)
    x,y,z=p['target'];board=box(x,y,z)
    board=holes(board,[(-90,-135),(90,-135),(-90,135),(90,135)],4.5,-.1,z+1)
    emit('P10','a4_target_backing','A4 靶纸背板',board,note='210×297×3；粘贴实际任务靶纸，本 CAD 不擅自定义命中半径。')
    foot=box(90,45,15).cut(box(60,z+.5,14,(0,0,3)))
    emit('P10','target_foot','靶板立式底座',foot,qty=2,note='两个底座托住背板下沿；现场加压重或夹紧。')

def build_carton():
    s=box(60,20,8).union(box(8,20,60,(-26,0,0)))
    emit('P12','flap_right_angle_gauge','翻盖 90° 复位角尺',s,qty=2,note='复位用，任务开始前撤掉。')
    s=box(55,55,6).union(box(4,45,24,(-20,0,0))).union(box(45,4,24,(0,-20,0)))
    s=s.cut(slot(20,4.5,8,(12,12,-1),45))
    s=magnets(s,[(-12,-12)])
    emit('P12','carton_corner_fixture','纸箱底角限位夹具',s,qty=4,note='4 个底角靠住纸箱底部；M4 螺栓/桌面夹具固定。不会固定上方翻盖。')

def build_camera():
    p=P['camera'];x,y,z=p['plate'];plate=box(x,y,z)
    for a in [-20,0,20]:plate=plate.cut(slot(44,3.4,z+2,(a,0,-1),90))
    emit('P13','d405_universal_plate','D405 通用长孔测量板',plate,note='并非已匹配 D405 的孔位；需要相机本体孔距、螺纹、线缆避让和夹爪安装空间实测。')
    stand=box(70,60,6).union(box(70,6,60,(0,27,0)))
    stand=bore(stand,p['tripod_clearance'],8,(0,0,-1))
    for x in [-20,20]:stand=stand.cut(slot(36,6.6,8,angle=90).rotate((0,0,0),(1,0,0),90).translate((x,31,34)))
    emit('P13','gemini_tripod_bracket','Gemini 2 L 门架角座',stand,note='1/4 英寸相机螺钉穿孔；相机朝向、底部孔位、型材 M6 滑块实测后安装。')
    d=p['flange_blank_od_assumed'];flange=cyl(d/2,p['flange_thickness_assumed']).cut(cyl(p['flange_center_assumed']/2,p['flange_thickness_assumed']+2,(0,0,-1)))
    for setname in ['robot_holes_xy','hand_holes_xy']:flange=holes(flange,p[setname],p['hole_d_assumed'],-1,p['flange_thickness_assumed']+2)
    emit('P13','rm75_hand_flange_blank','RM75-B—手接口测量毛坯',flange,variant='测量毛坯',note='无安装孔；OD70 / ID20 / 厚10 为占位尺寸。未核实孔位、定位止口、紧固深度、负载与刚度，不能用于带电机械臂承载。')

BUILDERS={'B32':build_printed_cards,'B33':build_card,'B25':build_printed_tube,'P01':build_pegs,'P02':build_drawer,'P03':build_cup,'P04':build_dustpan,'P05':build_racks,'P07':build_balls,'P08':build_knob,'P09':build_keypad,'P10':build_spray,'P12':build_carton,'P13':build_camera}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--groups',nargs='*');args=parser.parse_args()
    groups=args.groups or list(BUILDERS);start=time.time();errors=[]
    for group in groups:
        try:BUILDERS[group]()
        except Exception as error:
            import traceback
            traceback.print_exc();errors.append(dict(group=group,error=str(error)))
    spec_path=ROOT.parent.parent/'SPEC_v0.3.3.md'
    if not spec_path.exists():spec_path=ROOT/'reference/SPEC_v0.3.3.md'
    meta=dict(version='0.2',spec='v0.3.3',units='mm',printer=P['printer'],groups=[dict(id=k,name=v[0],tasks=v[1],status=v[2],notes=v[3]) for k,v in GROUPS.items() if k in groups],parts=PARTS,checks=CHECKS,errors=errors,elapsed_s=round(time.time()-start,1),parameters_sha256=hashlib.sha256((ROOT/'parameters.json').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'build_models.py').read_bytes()).hexdigest(),spec_sha256=hashlib.sha256(spec_path.read_bytes()).hexdigest())
    meta['user_prop_updates']=dict(source='PROP_UPDATES.md',sha256=hashlib.sha256((ROOT/'PROP_UPDATES.md').read_bytes()).hexdigest(),overrides=['H3 printed plastic card instead of PVC sheet','D3 printed tube instead of purchased PS/PP tube','D6 existing mineral-water bottle instead of printed square bottle'])
    meta['artifact_class']='manufacturing_prototype_with_user_material_substitutions'
    target=ROOT/('manifest.json' if not args.groups else 'manifest_'+'_'.join(groups)+'.json')
    target.write_text(json.dumps(meta,ensure_ascii=False,indent=2))
    print(json.dumps(dict(parts=len(PARTS),errors=errors,seconds=meta['elapsed_s']),ensure_ascii=False),flush=True)
    if errors or any(not c['pass_check'] for c in CHECKS):raise SystemExit(1)

if __name__=='__main__':main()
