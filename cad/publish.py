#!/usr/bin/env python3
"""Build previews, ZIPs and a dependency-free private CAD viewer from validated STLs."""
import argparse, csv, hashlib, json, math, shutil, zipfile
from pathlib import Path
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from assemblies import build_assemblies
from bundle_designs import build_bundle
from numba import njit

ROOT=Path(__file__).resolve().parent
PUBLIC=Path('/home/meow/SO101/outputs/cyberwork_bench/20261020_v033/public/cad')
COLORS=['#37b5a5','#f0ac64','#589ad4','#c486c8','#b4bc64']

@njit(cache=True)
def rasterize(xy,vertices,faces,colors,width,height):
    pixels=np.empty((height,width,3),dtype=np.uint8)
    pixels[:,:,0]=235;pixels[:,:,1]=240;pixels[:,:,2]=241
    depth=np.full((height,width),-1e30)
    for i in range(len(faces)):
        a,b,c=faces[i];x0,y0=xy[a];x1,y1=xy[b];x2,y2=xy[c]
        denominator=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
        if abs(denominator)<1e-10:continue
        xmin=max(0,int(math.floor(min(x0,x1,x2))));xmax=min(width-1,int(math.ceil(max(x0,x1,x2))))
        ymin=max(0,int(math.floor(min(y0,y1,y2))));ymax=min(height-1,int(math.ceil(max(y0,y1,y2))))
        for y in range(ymin,ymax+1):
            for x in range(xmin,xmax+1):
                wa=((y1-y2)*(x+.5-x2)+(x2-x1)*(y+.5-y2))/denominator
                wb=((y2-y0)*(x+.5-x2)+(x0-x2)*(y+.5-y2))/denominator
                wc=1-wa-wb
                if wa<-.000001 or wb<-.000001 or wc<-.000001:continue
                z=wa*vertices[a,2]+wb*vertices[b,2]+wc*vertices[c,2]
                if z>depth[y,x]:
                    depth[y,x]=z;pixels[y,x]=colors[i]
    return pixels

def preview(mesh,path,color='#37b5a5',size=(650,480)):
    v=mesh.vertices-mesh.bounds.mean(axis=0)
    az=math.radians(-35);el=math.radians(28)
    rz=np.array([[math.cos(az),-math.sin(az),0],[math.sin(az),math.cos(az),0],[0,0,1]])
    rx=np.array([[1,0,0],[0,math.sin(el),math.cos(el)],[0,-math.cos(el),math.sin(el)]])
    v=v@rz.T@rx.T
    scale=min((size[0]-90)/np.ptp(v[:,0]),(size[1]-90)/np.ptp(v[:,1]))
    xy=v[:,:2]*[scale,-scale]+np.array(size)/2
    faces=mesh.faces;depth=v[faces,2].mean(axis=1)
    normals=mesh.face_normals@rz.T@rx.T
    light=np.array([-.4,.7,.9]);light/=np.linalg.norm(light)
    shade=.55+.45*np.abs(normals@light)
    base=np.array([int(color[i:i+2],16) for i in [1,3,5]])
    colors=np.clip(shade[:,None]*base,0,255).astype(np.uint8)
    im=Image.fromarray(rasterize(xy,v,faces,colors,size[0],size[1]));draw=ImageDraw.Draw(im)
    draw.text((18,size[1]-25),'CAD / mm — model preview, not a printed sample',fill=(70,90,95))
    im.save(path)

def zip_paths(target,paths):
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for p in paths:z.write(p,p.relative_to(ROOT))

def main():
    global PUBLIC
    parser=argparse.ArgumentParser()
    parser.add_argument('--public-dir',type=Path,default=PUBLIC if PUBLIC.parent.exists() else ROOT/'site')
    PUBLIC=parser.parse_args().public_dir
    data=json.loads((ROOT/'manifest.json').read_text())
    if data['errors'] or any(not c['pass_check'] for c in data['checks']):raise SystemExit('Refuse publication: unresolved geometry checks')
    audit=json.loads((ROOT/'geometry_audit.json').read_text())
    if audit['passed']!=audit['total'] or audit.get('manifest_sha256')!=hashlib.sha256((ROOT/'manifest.json').read_bytes()).hexdigest():raise SystemExit('Run audit_models.py against the current manifest before publication')
    previews=ROOT/'previews';previews.mkdir(exist_ok=True)
    packages=ROOT/'packages';packages.mkdir(exist_ok=True)
    reference=ROOT/'reference';reference.mkdir(exist_ok=True)
    if (ROOT.parent.parent/'SPEC_v0.3.3.md').exists():shutil.copy2(ROOT.parent.parent/'SPEC_v0.3.3.md',reference/'SPEC_v0.3.3.md')
    shared=[ROOT/'README.md',ROOT/'PROP_UPDATES.md',ROOT/'parameters.json',ROOT/'build_models.py',ROOT/'requirements-lock.txt',reference/'SPEC_v0.3.3.md']
    assemblies=build_assemblies(data)
    for index,row in enumerate(data['parts']):
        mesh=trimesh.load_mesh(ROOT/row['files']['stl'],process=False)
        png=previews/(row['id']+'.png');preview(mesh,png,COLORS[index%len(COLORS)])
        row['preview']=str(png.relative_to(ROOT))
        # glTF/GLB uses metres, unlike millimetre-native STL/STEP.
        scene=trimesh.Scene(mesh.copy());scene.apply_scale(.001)
        glb=ROOT/row['files']['stl'].replace('.stl','.glb');glb.write_bytes(scene.export(file_type='glb'))
        row['files']['glb']=str(glb.relative_to(ROOT))
    for group in data['groups']:
        rows=[r for r in data['parts'] if r['group']==group['id']]
        group['part_count']=len(rows)
        group['preview']=next((r['preview'] for r in rows if r['variant']=='BASE'),rows[0]['preview'])
        if group['id'] in assemblies:
            a=assemblies[group['id']]
            img=previews/(group['id']+'_assembly.png');preview(a['mesh'],img)
            group['preview']=str(img.relative_to(ROOT));group['assembly_files']=a['files'];group['assembly_note']=a['scope']
        archive=packages/(group['id']+'.zip')
        zip_paths(archive,[ROOT/f for r in rows for f in r['files'].values()]+[ROOT/f for f in group.get('assembly_files',{}).values()]+shared)
        group['zip']=str(archive.relative_to(ROOT))
    data['paired_sets']=[
      dict(id='H3',name='卡片 + 卡槽',groups=['B32','B33'],zip='packages/H3_cards_and_slots.zip',description='四档 85×54 mm 卡片与对应槽座；BASE 先打 2 mm 卡片和 2 mm 卡槽。',base_print=[dict(part='card_t2',quantity=3),dict(part='card_slot_t2',quantity=1)]),
      dict(id='D3',name='试管 + 试管架 + V 托',groups=['B25','P05'],zip='packages/D3_tubes_and_rack.zip',description='Ø12×75 mm 空心封底试管，配四档孔架；BASE 用 Ø15 mm 导向架。',base_print=[dict(part='printed_tube_12x75',quantity=2),dict(part='rack_weight_base',quantity=1),dict(part='rack_weight_lid',quantity=1),dict(part='rack_guide_15',quantity=1),dict(part='tube_v_rest',quantity=2)]),
    ]
    for pair in data['paired_sets']:
        rows=[r for r in data['parts'] if r['group'] in pair['groups']]
        pair['part_ids']=[r['id'] for r in rows]
        packing=ROOT/('set_'+pair['id']+'.json');packing.write_text(json.dumps(pair,ensure_ascii=False,indent=2))
        associated=[g for g in data['groups'] if g['id'] in pair['groups']]
        zip_paths(ROOT/pair['zip'],[ROOT/f for r in rows for f in r['files'].values()]+[ROOT/f for g in associated for f in g.get('assembly_files',{}).values()]+shared+[packing])
        for group in associated:group['paired_set']=pair['id'];group['paired_zip']=pair['zip']
    data['prop_updates']='PROP_UPDATES.md'
    data['purchased_bottle']=dict(prop_id='P06',route='矿泉水瓶 + 原装盖',status='待实测；不在默认打印包',measurements='../procurement/existing_bottle_measurements.json')
    data['glb_units']='metres';data['physical_print_tested']=False
    (ROOT/'catalog.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
    with (ROOT/'parts.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['组','文件名','零件','档位','每套建议件数','打印包络mm','实体体积cm3','说明'])
        for r in data['parts']:w.writerow([r['group'],r['id'],r['name'],r['variant'],r['quantity'],'×'.join(map(str,r['dimensions_mm'])),r['solid_volume_cm3'],r['notes']])
    paths=[ROOT/n for n in ['parameters.json','build_models.py','publish.py','assemblies.py','audit_models.py','bundle_designs.py','geometry_audit.json','README.md','PROP_UPDATES.md','requirements-lock.txt','manifest.json','catalog.json','parts.csv','set_H3.json','set_D3.json']]
    paths += [ROOT/f for r in data['parts'] for f in r['files'].values()]
    paths += [ROOT/f for g in data['groups'] for f in g.get('assembly_files',{}).values()]
    paths += [reference/'SPEC_v0.3.3.md',ROOT/'index.html',ROOT/'style.css',ROOT/'viewer.js']
    zip_paths(packages/'cyberwork_plastic_cad_v0.2_h2s.zip',paths)
    PUBLIC.mkdir(parents=True,exist_ok=True)
    for name in ['models','previews','packages','assemblies']:shutil.copytree(ROOT/name,PUBLIC/name,dirs_exist_ok=True)
    for name in ['catalog.json','manifest.json','parts.csv','parameters.json','build_models.py','publish.py','assemblies.py','audit_models.py','geometry_audit.json','README.md','PROP_UPDATES.md','requirements-lock.txt','index.html','viewer.js','style.css','set_H3.json','set_D3.json']:shutil.copy2(ROOT/name,PUBLIC/name)
    # Overview of actual exported meshes, one representative per group.
    canvas=Image.new('RGB',(1600,math.ceil(len(data['groups'])/4)*350),(244,246,246));draw=ImageDraw.Draw(canvas)
    fontpath='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    font=ImageFont.truetype(fontpath,19) if Path(fontpath).exists() else ImageFont.load_default()
    for i,g in enumerate(data['groups']):
        x=(i%4)*400;y=(i//4)*350
        im=Image.open(ROOT/g['preview']);im.thumbnail((390,285));canvas.paste(im,(x+(400-im.width)//2,y))
        draw.text((x+14,y+288),g['id']+' '+g['name'],font=font,fill=(25,55,60))
        draw.text((x+14,y+315),f'{g["part_count"]} files / {g["status"]}',font=font,fill=(80,95,100))
    canvas.save(ROOT/'overview.png');shutil.copy2(ROOT/'overview.png',PUBLIC/'overview.png')
    build_bundle(ROOT,PUBLIC)
    print(json.dumps(dict(groups=len(data['groups']),parts=len(data['parts']),url='http://100.69.243.126:8765/cad/',zip_bytes=(packages/'cyberwork_plastic_cad_v0.2_h2s.zip').stat().st_size),ensure_ascii=False))

if __name__=='__main__':main()
