"""Illustrative BASE assemblies made from the exact exported parts.

Purchased hardware is omitted. These views explain placement, not complete
mechanical fit validation. STEP assembly and GLB scene both retain separate parts.
"""
import json, math
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parent
COLORS=[(.15,.65,.59,1),(.92,.62,.29,1),(.29,.53,.73,1),(.64,.41,.66,1)]

def build_assemblies(data):
    rows={r['id']:r for r in data['parts']};out=ROOT/'assemblies';out.mkdir(exist_ok=True)
    definitions={
      'B33':[('card_slot_t2',(0,0,0)),('card_t2',(0,1,36),((1,0,0),90))],
      'P01':[('round_base_24',(0,0,0)),('round_peg_60',(0,0,5))],
      'P02':[('index_base',(0,0,0)),('index_rotor',(0,0,8.5)),('cabinet_shell',(0,0,16.5)),('cabinet_roof',(0,0,162.5)),('drawer_tub',(0,-17,26.5)),('drawer_handle',(0,-142,91.5),((1,0,0),90))],
      'P03':[('weighted_cup',(0,0,0)),('cup_ballast_lid',(0,0,0))],
      'P05':[('rack_weight_base',(0,0,0)),('rack_weight_lid',(0,0,15)),('rack_guide_15',(0,0,18)),('printed_tube_12x75',(-11.5,0,18)),('printed_tube_12x75',(11.5,0,18)),('tube_v_rest',(-30,-60,0)),('tube_v_rest',(30,-60,0))],
      'P07':[('tray_3_balls',(0,0,40)),*[('tray_foot',(x,y,0)) for x in [-85,85] for y in [-75,75]],('weight_box_body',(0,145,0)),('weight_box_lid',(0,145,38)),('ball_ring_110',(0,-150,0))],
      'P08':[('knob_bearing_stand',(0,0,0)),('knob_50',(0,-11,75),((1,0,0),90)),('bearing_retainer',(0,-7,75),((1,0,0),90)),('bearing_retainer',(0,7,75),((1,0,0),-90)),('brake_riser',(0,32,8)),('friction_brake_block',(0,32,53)),('brake_pressure_shoe',(0,32,78))],
      'P09':[('keypad_body',(0,0,0)),('keypad_top',(0,0,76))],
      'P10':[('a4_target_backing',(0,1.5,151.5),((1,0,0),90)),('target_foot',(-60,0,0)),('target_foot',(60,0,0)),('spray_neck_front',(155,0,0)),('spray_neck_back',(155,0,0))],
    }
    result={}
    for group,entries in definitions.items():
        assembly=cq.Assembly(name=group+'_illustrative');scene=trimesh.Scene()
        for i,entry in enumerate(entries):
            key,xyz,*rotation=entry;r=rows[key]
            s=cq.importers.importStep(str(ROOT/r['files']['step'])).translate(tuple(r['print_origin_mm']))
            mesh=trimesh.load_mesh(ROOT/r['files']['stl'],process=True);mesh.apply_translation(r['print_origin_mm'])
            if r['print_rotation']:
                axis,angle=r['print_rotation'];s=s.rotate((0,0,0),tuple(axis),-angle)
                mesh.apply_transform(trimesh.transformations.rotation_matrix(math.radians(-angle),axis))
            if rotation:
                axis,angle=rotation[0];s=s.rotate((0,0,0),axis,angle)
                mesh.apply_transform(trimesh.transformations.rotation_matrix(math.radians(angle),axis))
            s=s.translate(xyz);mesh.apply_translation(xyz)
            color=COLORS[i%len(COLORS)];mesh.visual.face_colors=np.array(color)*255
            assembly.add(s,name=f'{key}_{i}',color=cq.Color(*color))
            scene.add_geometry(mesh,node_name=f'{key}_{i}')
        step=out/(group+'.step');assembly.export(str(step))
        glb=out/(group+'.glb');scene_m=scene.copy();scene_m.apply_scale(.001);glb.write_bytes(scene_m.export(file_type='glb'))
        # Mesh for the thumbnail only; retain individual colors in the GLB/STEP files.
        mesh=scene.to_mesh()
        result[group]=dict(scene=scene,mesh=mesh,files={'step':str(step.relative_to(ROOT)),'glb':str(glb.relative_to(ROOT))},scope='装配位置示意；未显示外购轴承、滑轨、紧固件和电子件；不是完整机械验收')
    return result
