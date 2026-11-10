from pathlib import Path
import json,sys,shutil
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import geometry,rgba,pal,gfx,parts,component
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256
from scripts.build_riko_idle import BEAM_IN_V2_SCOPE,patch_frames
from scripts.repack_zero import read_inputs
from src.psx_beam_in import derive_beam_frames,validate_beam_frames
D=Path(__file__).parent;P=D.parent/'shippuuga_v1';B=ROOT/'out/ver_buki_riko/riko_bank1_20261025T134737617192Z'
rec=json.loads((P/'motion_set.json').read_text());registration=json.loads((D/'key_registration.json').read_text());regs={r['frame']:r for r in registration['keys']};worlds={k:v.copy() for k,v in np.load(D/'key_worlds.npz').items()}
for r in rec['frames'].values():shutil.copyfile(P/r['file'],D/r['file'])
p=rec['launch_production']['preview_palette'];shutil.copyfile(P/p['file'],D/p['file'])
frames={};placements={}
for n in range(249,254):
    if regs[n]['outside'] or abs(regs[n]['feet_center_error'])>.5:raise ValueError(('Invalid registration',n))
    size,bounds,safe=geometry(n);w=worlds[str(n)];a=w[96+bounds[1]:96+bounds[3],96+bounds[0]:96+bounds[2]]
    frames[n]=(a.tobytes(),size);placements[str(n)]=regs[n]['head_world']
if len({frames[n][0] for n in range(249,254)})!=5:raise ValueError('Arrival needs five distinct colored poses')
if np.array_equal(worlds['253'],worlds['idle']):raise ValueError('Settling pose must animate into idle')
frames.update(derive_beam_frames(gfx,parts,frames[249],dynamic=True))
placements.update({'247':placements['249'],'248':placements['249']})
checks=[]
for n in sorted(frames):
    data,size=frames[n];_,bounds,safe=geometry(n);w=np.zeros((192,192),np.uint8);w[96+bounds[1]:96+bounds[3],96+bounds[0]:96+bounds[2]]=np.frombuffer(data,np.uint8).reshape(size[1],size[0])
    bad=int(np.count_nonzero((w!=0)&~safe))
    if bad:raise ValueError(('Outside phase',n,bad))
    groups=component(w!=0)
    if len(groups)!=1:raise ValueError(('Detached cape or body',n,[len(g) for g in groups]))
    worlds[str(n)]=w;p=D/f'frame_{n:03d}.png';save_image(data,size,pal,p);rec['frames'][str(n)]={'file':p.name,'sha256':sha256(p.read_bytes())}
    yy,xx=np.nonzero(w);checks.append({'frame':n,'head_world':placements[str(n)],'floor':int(yy.max())-96,'height':int(yy.max()-yy.min()+1),'outside':bad,'components':1,'opaque_pixels':len(yy)})
rec['scope']=BEAM_IN_V2_SCOPE;rec['body_standard']['head_world_positions'].update(placements)
rec['beam_in_production']={'version':2,'source_scale':.105,'source_art_sha256':{p:sha256((D/p).read_bytes()) for p in ('generated_keys.png','generated_compact.png')},'keys':list(range(249,254)),
    'idle_source':(B/'idle_147.png').relative_to(ROOT).as_posix(),'idle_source_sha256':sha256((B/'idle_147.png').read_bytes()),
    'foot_registration':registration,'pure_beam_frames_preserved':list(range(53,61)),
    'derived':validate_beam_frames(gfx,parts,frames,dynamic=True)}
(D/'motion_set.json').write_text(json.dumps(rec,indent=2),'utf8');(D/'art_checks.json').write_text(json.dumps(checks,indent=2),'utf8')
_,_,arc,gm,gfx,parts,_=read_inputs(ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z');palette=(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/candidate_palette.bin').read_bytes()
_,report=patch_frames(arc,gm,gfx,parts,frames,palette);(D/'new_frames_poc.json').write_text(json.dumps(report,indent=2),'utf8')
board=Image.new('RGBA',(8*270,335),(32,36,48));draw=ImageDraw.Draw(board)
for i,key in enumerate([*map(str,range(247,254)),'idle']):
    pic=rgba(worlds[key]).crop((51,46,141,142)).resize((270,288),Image.Resampling.NEAREST)
    board.alpha_composite(pic,(270*i,28));draw.text((270*i+4,4),key+' STATIC',fill='white');draw.line((270*i,28+74*3,270*(i+1)-1,28+74*3),fill=(90,110,140),width=1)
board.save(D/'body_review.png');np.savez(D/'final_worlds.npz',**worlds)
sequence=[(247,2),(248,2),(249,2),(250,3),(251,12),(252,3),(253,3),('idle',60)]
for label,mult in [('actual_timing',1),('slow_review',4)]:
    images=[];durations=[]
    for n,t in sequence:
        p=Image.new('RGBA',(384,384),(32,36,48));p.alpha_composite(rgba(worlds[str(n)]).crop((48,48,144,144)).resize((384,384),Image.Resampling.NEAREST));images.append(p.convert('RGB'));durations.append(round(t*1000/60*mult))
    images[0].save(D/(label+'.gif'),save_all=True,append_images=images[1:],duration=durations,loop=0)
print(json.dumps({'art':checks,'compression':report['compression']}))
