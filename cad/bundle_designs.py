#!/usr/bin/env python3
"""Package current CAD sources and all parts; related parts live in nested ZIPs.

No geometry is regenerated. Membership is explicit and checked against the
current catalog, preventing omitted parts, duplicates and obsolete bottle files.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,shutil,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PUBLIC=Path('/home/meow/SO101/outputs/cyberwork_bench/20261020_v033/public/cad')
ARCHIVE='CyberWork_print_designs_v0.2_organized.zip'
TOP='CyberWork_打印设计文件_v0.2'

# The two multi-group sets are kept intact. P07 is split by actual physical use.
FAMILIES=[
 ('H3_卡片与卡槽','配套',['B32','B33'],None,['B33'],'先打印 card_t2 ×3、card_slot_t2 ×1。其他厚度配同编号卡槽。'),
 ('D3_试管_试管架_V形管托','配套',['B25','P05'],None,['P05'],'BASE：printed_tube_12x75 ×2、rack_weight_base ×1、rack_weight_lid ×1、rack_guide_15 ×1、tube_v_rest ×2。其他孔径是替换的阶梯档。'),
 ('S2_插销与孔座','配套',['P01'],None,['P01'],'先打印 peg_fit_coupon；BASE 用 round_peg_60 与 round_base_24。其余孔径、方销和长销是阶梯/OOD 备选。'),
 ('S3_抽屉柜_把手_分度转台','配套',['P02'],None,['P02'],'柜壳、顶板、抽屉、把手、底盘、转盘各 1。滑轨、紧固件外购，接口待测。'),
 ('S4_配重杯与底盖','配套',['P03'],None,['P03'],'weighted_cup 与 cup_ballast_lid 各 1；配重和螺钉另备。'),
 ('H5_球托盘与脚柱','配套',['P07'],'tray_',[],'BASE：tray_3_balls ×1、tray_foot ×4。2/4/5 球托盘为替换档；球另购。'),
 ('H6_配重盒与盒盖','配套',['P07'],'weight_box_',[],'weight_box_body 与 weight_box_lid 各 1；装配后按要求配重。'),
 ('H4_旋钮台与轴系支架','配套',['P08'],None,['P08'],'BASE 用 knob_50；knob_80 为 OOD。bearing_retainer 打印 2 个，其余基础结构按清单；轴承、轴、电位器和螺钉另购。'),
 ('H6_四键键盘外壳与控制板座','配套',['P09'],None,['P09'],'外壳、面板、PCB 座各 1；按钮和控制板另购，安装孔待实测。'),
 ('H2_喷壶改装夹件与靶板支架','配套',['P10'],None,['P10'],'各夹环和开关支架按件打印；A4 背板 1、target_foot ×2。喷壶、激光、开关接口待实测。'),
 ('H7_纸箱复位与底角夹具','配套',['P12'],None,[],'flap_right_angle_gauge ×2、carton_corner_fixture ×4；纸箱另购，复位角尺在任务开始前撤下。'),
 ('S5_薄口簸箕','独立',['P04'],None,[],'独立簸箕模型；磁铁另购。'),
 ('H1_防滚球托_四种尺寸','独立',['P07'],'ball_ring_',[],'按所购球的尺寸选择 90/110/130/150 之一，BASE 为 ball_ring_110。'),
 ('P13_相机支架与法兰毛坯_需实测','独立',['P13'],None,[],'通用相机接口草模和无孔法兰毛坯；需测量真实设备孔位后修改。'),
]

def csv_bytes(rows):
    stream=io.StringIO(newline='');writer=csv.writer(stream)
    writer.writerow(['文件名','零件名称','原物料编号','档位','原模型建议件数','打印尺寸mm','说明'])
    for row in rows:writer.writerow([row['id'],row['name'],row['group'],row['variant'],row['quantity'],' × '.join(map(str,row['dimensions_mm'])),row['notes']])
    return stream.getvalue().encode('utf-8-sig')

def part_entries(root,rows,assemblies,description,name):
    entries={}
    for row in rows:
        for extension,folder in [('stl','STL_毫米'),('step','STEP_毫米'),('glb','GLB_预览用_米')]:
            entries[f'{folder}/{row["id"]}.{extension}']=(root/row['files'][extension]).read_bytes()
        entries['预览图/'+row['id']+'.png']=(root/row['preview']).read_bytes()
    for assembly in assemblies:
        for extension in ['step','glb']:
            entries['装配示意/'+assembly+'.'+extension]=(root/'assemblies'/(assembly+'.'+extension)).read_bytes()
        preview=root/'previews'/(assembly+'_assembly.png')
        if preview.exists():entries['装配示意/'+assembly+'.png']=preview.read_bytes()
    entries['零件清单.csv']=csv_bytes(rows)
    entries['零件数据.json']=json.dumps(rows,ensure_ascii=False,indent=2).encode('utf-8')
    entries['先读说明.txt']=(f'{name}\n\n{description}\n\n'
        'STL 和 STEP 以毫米导出；GLB 只用于三维预览，单位为米。STL 是各自独立的打印件，不是已排盘的 G-code。\n'
        '“原模型建议件数”可能包含备份或后续数量；首批按上面 BASE 说明打印，不要把所有档位同时作为一套打印。\n'
        '需修改尺寸时，使用总包“01_可编辑设计源文件”中的 build_models.py 和 parameters.json；也可以用 CAD 软件编辑 STEP。\n'
        '文件已做几何检查，尚未实体试印；实际配合及待测接口状态见各零件清单和完整装配说明。\n').encode('utf-8')
    entries['完整打印与装配说明.md']=(root/'README.md').read_bytes()
    return entries

def zip_bytes(entries):
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name,data in entries.items():archive.writestr(name,data)
    return buf.getvalue()

def build_bundle(root=ROOT,public=PUBLIC):
    catalog=json.loads((root/'catalog.json').read_text())
    parts=catalog['parts'];by_id={p['id']:p for p in parts};seen=set();index=[];entries={}
    for name,kind,groups,prefix,assemblies,description in FAMILIES:
        selected=[p for p in parts if p['group'] in groups and (prefix is None or p['id'].startswith(prefix))]
        if not selected:raise ValueError('Empty family: '+name)
        for row in selected:
            if row['id'] in seen:raise ValueError('Duplicated part: '+row['id'])
            seen.add(row['id'])
            if hashlib.sha256((root/row['files']['stl']).read_bytes()).hexdigest()!=row['sha256']:raise ValueError('STL changed since validation: '+row['id'])
        contents=part_entries(root,selected,assemblies,description,name)
        if kind=='配套':
            location=f'02_配套打印件_小压缩包/{name}.zip'
            entries[location]=zip_bytes(contents)
        else:
            location=f'03_独立打印件/{name}'
            for relative,data in contents.items():entries[location+'/'+relative]=data
        index.append(dict(name=name,type=kind,path=location,part_ids=[r['id'] for r in selected],base_print_note=description))
    if seen!=set(by_id):raise ValueError('Unpackaged parts: '+str(set(by_id)-seen))
    if any(p['group']=='P06' for p in parts):raise ValueError('Obsolete printed bottle is not part of the current selection')
    source_files=['build_models.py','parameters.json','assemblies.py','audit_models.py','publish.py','bundle_designs.py',
                  'requirements-lock.txt','README.md','PROP_UPDATES.md','reference/SPEC_v0.3.3.md',
                  'index.html','viewer.js','style.css','manifest.json','catalog.json','geometry_audit.json','parts.csv',
                  'set_H3.json','set_D3.json']
    for name in source_files:entries['01_可编辑设计源文件/'+name]=(root/name).read_bytes()
    entries['04_总清单与预览/全部零件.csv']=csv_bytes(parts)
    entries['04_总清单与预览/模型总览.png']=(root/'overview.png').read_bytes()
    entries['04_总清单与预览/几何检查.json']=(root/'geometry_audit.json').read_bytes()
    index_data=dict(version=catalog['version'],parts=len(parts),nested_zips=sum(x['type']=='配套' for x in index),families=index)
    entries['04_总清单与预览/分包索引.json']=json.dumps(index_data,ensure_ascii=False,indent=2).encode('utf-8')
    listing='\n'.join(f'- {x["path"]}：{len(x["part_ids"])} 个独立模型' for x in index)
    readme=f'''CyberWork 打印设计文件 v0.2 · H2S · 整理总包

本包包含当前选择的 {len(parts)} 个独立零件模型。配套件已经装成 {index_data['nested_zips']} 个小 ZIP；其余独立件分文件夹放置。每个零件只在所属的小 ZIP 或独立文件夹中收录一次。

1. 只需打印：打开 02_配套打印件_小压缩包，解压要做的那一套，使用 STL_毫米。独立件在 03_独立打印件。
2. 想编辑形状：使用小包内 STEP_毫米。STEP 是可供 CAD 软件编辑的几何文件。
3. 想改参数并重建：01_可编辑设计源文件包含实际建模源码 build_models.py、尺寸参数 parameters.json 和依赖锁文件。按其中 README 安装 CAD 环境，运行 build_models.py → audit_models.py → publish.py，会生成新的 models/ 与装配文件；不必手动合并各小包的 STL。
4. 每套先读“先读说明.txt”和“零件清单.csv”。厚度/孔径阶梯是备选档，先按 BASE 数量试印。
5. 卡片与卡槽放在同一小包；试管、架体和 V 托也在同一小包。托盘与脚柱、盒体与盒盖等配套件同样放在一起。

STL / STEP 的单位为毫米；GLB 的单位为米，仅供预览。装配示意不包括外购的滑轨、螺钉、轴承、电子器件。
所有文件仍是尚未实体试印的设计原型，接口草模及法兰毛坯按原说明保留“需实测”状态。
拧瓶盖任务已经改用现成矿泉水瓶与原装盖，因此本总包不含旧打印方瓶或瓶盖。

目录索引：
{listing}
'''
    entries['00_先读说明.txt']=readme.encode('utf-8')
    entries['04_总清单与预览/SHA256SUMS.txt']=''.join(f'{hashlib.sha256(v).hexdigest()}  {k}\n' for k,v in entries.items()).encode('utf-8')
    package=root/'packages'/ARCHIVE;package.parent.mkdir(exist_ok=True)
    temporary=package.with_suffix('.zip.tmp')
    temporary.write_bytes(zip_bytes({TOP+'/'+name:data for name,data in entries.items()}))
    # Audit the final bytes, including nested archives, rather than assuming membership.
    found=[];nested=0
    with zipfile.ZipFile(temporary) as archive:
        if archive.testzip() is not None:raise ValueError('Outer ZIP CRC failed')
        for info in archive.infolist():
            if info.filename.endswith('.zip'):
                nested+=1
                with zipfile.ZipFile(io.BytesIO(archive.read(info))) as inner:
                    if inner.testzip() is not None:raise ValueError('Inner ZIP CRC failed: '+info.filename)
                    for path in inner.namelist():
                        if path.startswith('STL_毫米/') and path.endswith('.stl'):
                            key=Path(path).stem;found.append(key)
                            if hashlib.sha256(inner.read(path)).hexdigest()!=by_id[key]['sha256']:raise ValueError('Nested STL mismatch: '+key)
            elif '/STL_毫米/' in info.filename and info.filename.endswith('.stl'):
                key=Path(info.filename).stem;found.append(key)
                if hashlib.sha256(archive.read(info)).hexdigest()!=by_id[key]['sha256']:raise ValueError('Standalone STL mismatch: '+key)
    if len(found)!=len(parts) or set(found)!=set(by_id) or len(found)!=len(set(found)):raise ValueError('Final archive coverage mismatch')
    temporary.replace(package)
    result=dict(version=catalog['version'],archive=ARCHIVE,parts=len(found),nested_zips=nested,standalone_families=sum(x['type']=='独立' for x in index),bytes=package.stat().st_size,sha256=hashlib.sha256(package.read_bytes()).hexdigest(),crc_verified=True,stl_hashes_verified=True,all_parts_once=True)
    (root/'organized_bundle_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    (root/'organized_bundle_index.json').write_text(json.dumps(index_data,ensure_ascii=False,indent=2))
    if public is not None:
        (public/'packages').mkdir(parents=True,exist_ok=True)
        shutil.copy2(package,public/'packages'/ARCHIVE)
        for name in ['organized_bundle_audit.json','organized_bundle_index.json','bundle_designs.py']:shutil.copy2(root/name,public/name)
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--public-dir',type=Path,default=PUBLIC if PUBLIC.exists() else None);args=parser.parse_args()
    print(json.dumps(build_bundle(public=args.public_dir),ensure_ascii=False))
