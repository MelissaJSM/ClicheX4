from pathlib import Path
import sys,json,shutil
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from work.ver_buki_riko.art_pilot.wall_saber_v1.fit_wall import original,rgba,pal,gfx,parts
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import component
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256
from src.psx_frame_edit import read_indexed_png
from src.psx_bank_patch import patch_bank
from src.psx_victory import BODY,KEYS,EFFECTS,SCOPE,HEAD_VIEWS,derive_flashes,validate_victory
D=Path(__file__).parent;P=D.parent/'raijingeki_v1';rec=json.loads((P/'recipe.json').read_text())
worlds={k:v.copy() for k,v in np.load(D/'key_worlds.npz').items()};regs={r['frame']:r for r in json.loads((D/'key_registration.json').read_text())}
for r in rec['frames'].values():shutil.copyfile(P/r['file'],D/r['file'])
for name in ('static_effects.json','effect_palette.bin','effect_23.png','effect_24.png'):shutil.copyfile(P/name,D/name)
frames={};heads={}
for n in KEYS:
    if regs[n]['outside']:raise ValueError(('Outside key',n))
    a,b,_=original(n);w=worlds[str(n)];picture=w[96+b[1]:96+b[3],96+b[0]:96+b[2]];frames[n]=(picture.tobytes(),(picture.shape[1],picture.shape[0]));heads[str(n)]=regs[n]['head_world']
frames.update(derive_flashes(gfx,parts,frames[3]));heads.update({'7':heads['3'],'8':heads['3']})
checks=[]
for n in sorted(BODY):
    data,size=frames[n];a,b,safe=original(n);w=np.zeros((192,192),np.uint8);w[96+b[1]:96+b[3],96+b[0]:96+b[2]]=np.frombuffer(data,np.uint8).reshape(size[1],size[0])
    bad=int(np.count_nonzero((w!=0)&~safe));groups=component(w!=0)
    if bad or len(groups)!=1:raise ValueError(('Invalid body/flash',n,bad,[len(g) for g in groups]))
    p=D/f'bank1_{n:03d}.png';save_image(data,size,pal,p);rec['frames'][str(n)]={'file':p.name,'sha256':sha256(p.read_bytes())};rec['body_standard']['head_world_positions'][str(n)]=heads[str(n)];rec['body_standard']['head_sizes'][str(n)]=[23,19];worlds[str(n)]=w
    yy,xx=np.nonzero(w);checks.append({'frame':n,'head_world':heads[str(n)],'floor':int(yy.max())-96,'height':int(yy.max()-yy.min()+1),'outside':bad,'components':1,'opaque_pixels':len(yy)})
for n in EFFECTS:
    a,b,_=original(n);p=D/f'bank1_{n:03d}.png';save_image(a.tobytes(),(a.shape[1],a.shape[0]),pal,p);rec['frames'][str(n)]={'file':p.name,'sha256':sha256(p.read_bytes())}
preserved=set(rec['preserved_effect_frames'])|EFFECTS
full={int(k):read_indexed_png(D/v['file'],pal) for k,v in rec['frames'].items()};_,packing=patch_bank(gfx,parts,1,5,full,preserved,clear_unreferenced=True)
rec.update(scope=SCOPE,preserved_effect_frames=sorted(preserved),victory_head_views=HEAD_VIEWS,victory_source_scale=regs[3]['scale'],victory_source_sha256={name:sha256((D/name).read_bytes()) for name in ('generated_corrected.png','generated_gesture.png')},victory_parent_sha256=sha256((P/'recipe.json').read_bytes()),victory_checks=validate_victory(gfx,parts,frames),art_revision='victory_beam_out_v1')
(D/'recipe.json').write_text(json.dumps(rec,indent=2),'utf8');(D/'art_checks.json').write_text(json.dumps(checks,indent=2),'utf8');(D/'packing_checks.json').write_text(json.dumps(packing,indent=2),'utf8');np.savez(D/'final_worlds.npz',**worlds)
board=Image.new('RGBA',(9*240,300),(32,36,48));draw=ImageDraw.Draw(board)
for n in sorted(BODY):
    board.alpha_composite(rgba(worlds[str(n)]).crop((56,48,136,138)).resize((240,270),Image.Resampling.NEAREST),(n*240,25));draw.text((n*240+5,5),str(n)+' STATIC',fill='white')
board.save(D/'body_review.png')
for label,sequence in [('victory',[(0,2),(1,2),(2,2),(3,2),(4,3),(5,6),(6,96)]),('departure',[(0,2),(1,2),(2,2),(3,4),(7,2),(8,2),(9,2),(10,2),(11,12)])]:
    images=[];durations=[]
    for n,t in sequence:
        if str(n) not in worlds:
            a,b,_=original(n);w=np.zeros((192,192),np.uint8);w[96+b[1]:96+b[3],96+b[0]:96+b[2]]=a
        else:w=worlds[str(n)]
        p=Image.new('RGBA',(384,384),(32,36,48));p.alpha_composite(rgba(w).crop((48,24,144,120)).resize((384,384),Image.Resampling.NEAREST));images.append(p.convert('RGB'));durations.append(round(t*1000/60))
    images[0].save(D/(label+'_timing_preview.gif'),save_all=True,append_images=images[1:],duration=durations,loop=0)
print(json.dumps({'art':checks,'new_compression':[r for r in packing['compression'] if any(n<14 for n in r['frames'])]}))
