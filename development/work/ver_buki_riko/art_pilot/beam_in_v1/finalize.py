from pathlib import Path
import json,sys,shutil
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import geometry,rgba,pal,gfx,parts,front,component
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256
from scripts.build_riko_idle import BEAM_IN_SCOPE,check_motion_scale,patch_frames
from scripts.repack_zero import read_inputs
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.psx_beam_in import BEAM_BODY_FRAMES,derive_beam_frames,validate_beam_frames
D=Path(__file__).parent;P=D.parent/'shippuuga_v1';B=ROOT/'out/ver_buki_riko/riko_bank1_20261025T134737617192Z'
rec=json.loads((P/'motion_set.json').read_text());regs={r['frame']:r for r in json.loads((D/'key_registration.json').read_text())};keys=np.load(D/'key_pixels.npz');bank=graphics_bank(gfx,0)
for r in rec['frames'].values():shutil.copyfile(P/r['file'],D/r['file'])
p=rec['launch_production']['preview_palette'];shutil.copyfile(P/p['file'],D/p['file'])
frames={};placements={};worlds={};checks=[]
for n in [251,252,253]:
    size,bounds,safe=geometry(n);w=np.zeros((192,192),np.uint8)
    if n==253:
        a=np.array(Image.open(B/'idle_147.png'));x,y=-24,-24;hp=[11,0]
    else:
        r=regs[n];a=keys[str(n)].copy();hp=r['head_local'];x,y=r['position'];x-=2
        # The fixed native head includes its accessory; remove extra generated
        # pixels above it instead of leaving a second floating ornament.
        a[:hp[1]]=0
    h,width=a.shape;w[96+y:96+y+h,96+x:96+x+width]=a
    bad=int(np.count_nonzero((w!=0)&~safe))
    if bad:raise ValueError(('Outside key',n,bad))
    a=w[96+bounds[1]:96+bounds[3],96+bounds[0]:96+bounds[2]]
    frames[n]=(a.tobytes(),size);placements[str(n)]=[x+hp[0],y+hp[1]];worlds[n]=w
    yy,xx=np.nonzero(w);checks.append({'frame':n,'head_world':placements[str(n)],'floor':int(yy.max())-96,'height':int(yy.max()-yy.min()+1),'outside':bad,'components':[len(c) for c in component(w!=0)],'opaque_pixels':len(yy)})
frames.update(derive_beam_frames(gfx,parts,frames[251]))
for n in range(247,251):placements[str(n)]=placements['251']
for n in sorted(frames):
    data,size=frames[n];_,bounds,safe=geometry(n);w=np.zeros((192,192),np.uint8);w[96+bounds[1]:96+bounds[3],96+bounds[0]:96+bounds[2]]=np.frombuffer(data,np.uint8).reshape(size[1],size[0])
    if np.any((w!=0)&~safe):raise ValueError(('Outside derived phase',n,int(np.count_nonzero((w!=0)&~safe))))
    worlds[n]=w;p=D/f'frame_{n:03d}.png';save_image(data,size,pal,p);rec['frames'][str(n)]={'file':p.name,'sha256':sha256(p.read_bytes())}
rec['scope']=BEAM_IN_SCOPE;rec['body_standard']['head_world_positions'].update(placements)
rec['beam_in_production']={'source_scale':.09,'source_art_sha256':sha256((D/'generated_keys.png').read_bytes()),'keys':[251,252],
    'idle_transition_frame':253,'idle_source':str(B/'idle_147.png'),'idle_source_sha256':sha256((B/'idle_147.png').read_bytes()),
    'pure_beam_frames_preserved':list(range(53,61)),'derived':validate_beam_frames(gfx,parts,frames)}
(D/'motion_set.json').write_text(json.dumps(rec,indent=2),'utf8');(D/'art_checks.json').write_text(json.dumps(checks,indent=2),'utf8')
# Small local POC before writing any full disc: originals roundtrip and new
# streams must fit the exact original lengths. Includes all shared references.
profile,project,arc,gm,gg,pp,zero=read_inputs(ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z');palette=(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/candidate_palette.bin').read_bytes()
original={}
for n in frames:
    f=bank['frames'][n];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data;original[n]=compose_indices(raw,f['tile_count'],composition_frame(parts,0,n))[:2]
old,_=patch_frames(arc,gm,gfx,parts,original,palette)
changed,report=patch_frames(arc,gm,gfx,parts,frames,palette)
(D/'new_frames_poc.json').write_text(json.dumps(report,indent=2),'utf8')
board=Image.new('RGBA',(8*240,300),(32,36,48));draw=ImageDraw.Draw(board)
for i,n in enumerate(range(247,255)):
    w=worlds[n] if n<254 else worlds[253]
    board.alpha_composite(rgba(w).crop((56,48,136,136)).resize((240,264),Image.Resampling.NEAREST),(240*i,24));draw.text((240*i+4,4),str(n) if n<254 else 'APPROVED IDLE',fill='white')
board.save(D/'body_review.png');np.savez(D/'final_worlds.npz',**{str(n):w for n,w in worlds.items()})
seq=[(247,2),(248,2),(249,2),(250,3),(251,12),(252,3),(253,3),(253,70)]
gif=[];dur=[]
for n,ticks in seq:
    panel=Image.new('RGBA',(288,288),(34,38,48));panel.alpha_composite(rgba(worlds[n]).crop((48,48,144,144)).resize((288,288),Image.Resampling.NEAREST));gif.append(panel.convert('RGB'));dur.append(round(ticks*1000/60))
gif[0].save(D/'arrival_preview.gif',save_all=True,append_images=gif[1:],duration=dur,loop=0)
print(json.dumps({'art':checks,'compression':report['compression']}))
