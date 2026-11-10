"""검증된 낙봉파 돔 배경에 새 공통 몸체를 등록한다.23/24 외 보존."""
from pathlib import Path
import sys,json,struct,os,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from scripts.c01_audio_build import read_disc
from scripts.extract_zero import save_image
from scripts.rakuhouha_static import apply_static_set
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static,patch_static
from src.psx_disc import file_hash
W=ROOT/'work/sprite_style_unification_20261107';D=W/'riko';OUT=D/'prepared_burst_final_v1'
P=D/'prepared_burst_variants_v2/PL01_U.ARC';BEFORE=D/'prepared_ceremony_v2/PL01_U.ARC'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert not OUT.exists();arc=P.read_bytes();before=BEFORE.read_bytes()
assert sha(arc)=='46d1b1eeacc9c113b02db40ca84165d8b15c7976324e518640ffdd5f4491f4db'
assert sha(before)=='590ed75799910795db7f237688bbd10ef3a282a7d12910956d798f497e67f818'
original_path=ROOT/'MegaMan X4.bin';assert file_hash(original_path)=='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
original=read_disc(original_path,('PL01_U.ARC',))[0]['PL01_U.ARC']
otex=entry(original,0x10206);texture=entry(arc,0x10206);parts=entry(arc,3)
zero=np.roll(render(original,1,5,182)[0],-1,axis=0)
recipe_old=json.loads((ROOT/'work/ver_buki_riko/art_pilot/rakuhouha_v2/static_effects.json').read_text('utf8'))
palpath=ROOT/'work/ver_buki_riko/art_pilot/rakuhouha_v2/effect_palette.bin';pal=palpath.read_bytes();words=struct.unpack('<16H',pal)
assert sha(pal)==recipe_old['palette_sha256']
frames={};comps={};proof=[];previews={}
for n,body in ((23,185),(24,182)):
    comp=composition_frame(parts,6,n);comps[n]=comp
    data,size,bounds,sources=compose_static(otex,comp);a=np.frombuffer(data,np.uint8).reshape(size[1],size[0])
    current=np.frombuffer(compose_static(texture,comp)[0],np.uint8).reshape(a.shape)
    x0,y0,x1,y1=[160+v for v in bounds]
    old=(zero[y0:y1,x0:x1]>0)&(a!=0);old[:max(0,-17-bounds[1])]=False
    locations={}
    for group in sources:
        for loc in group:locations[loc]=locations.get(loc,0)+1
    unique=np.array([len(q)==1 and locations[q[0]]==1 for q in sources]).reshape(a.shape)
    assert not np.any(old&~unique)
    clean=a.copy()
    for y,x in zip(*np.nonzero(old)):
        mirror=-12-(x+bounds[0])-bounds[0]
        if 0<=mirror<size[0] and not old[y,mirror] and a[y,mirror]:value=a[y,mirror]
        else:
            available=np.flatnonzero((~old[y])&(a[y]!=0))
            if not len(available):clean[y,x]=0;continue
            closest=available[np.argsort(abs(available-x),kind='stable')[:2]];value=a[y,closest[0]]
            if n==24 and 13 in a[y,available]:value=13
        clean[y,x]=value
    remap=np.array([recipe_old['frames'][str(n)]['tint_map'][str(i)] for i in range(16)],np.uint8)
    def composite(body_world):
        pixels=body_world[y0:y1,x0:x1];mask=(pixels>0)&(a>0)&unique
        out=clean.copy();out[mask]=remap[pixels[mask]]
        return out,mask
    predicted,prior_mask=composite(render(before,1,5,body)[0])
    old_errors=int(np.count_nonzero(predicted!=current))
    assert old_errors==0,f'Existing effect {n} cannot be exactly reconstructed: {old_errors}'
    after,new_mask=composite(render(arc,1,5,body)[0])
    assert np.array_equal(after[~(prior_mask|new_mask)],current[~(prior_mask|new_mask)])
    assert np.array_equal(after==0,current==0)
    frames[n]=(after.tobytes(),size);previews[n]=(current,after)
    proof.append({'ref':n,'body_ref':body,'bounds':bounds,'old_effect_exactly_reconstructed':True,
        'body_world_sha256':sha(render(arc,1,5,body)[0].tobytes()),'changed_pixels':int(np.count_nonzero(after!=current)),
        'outside_old_or_new_body_exact':True,'entire_effect_alpha_exact':True,'tint_map':remap.tolist()})
new_texture=patch_static(texture,comps,frames)
users=[]
for b in (1,2,3,4,6):
    for n in range(composition_frame(parts,b,0)['bank_frame_count']):
        cp=composition_frame(parts,b,n)
        tiles={p['page']*256+p['tile'] for p in cp['parts']}
        altered=any(texture[(t//16*16+y)*128+t%16*8:(t//16*16+y)*128+t%16*8+8]
                    !=new_texture[(t//16*16+y)*128+t%16*8:(t//16*16+y)*128+t%16*8+8]
                    for t in tiles for y in range(16))
        if altered:users.append([b,n])
assert users==[[6,23],[6,24]]
OUT.mkdir();(OUT/'palette.bin').write_bytes(pal)
bound_frames={}
for n,(pixels,size) in frames.items():
    save_image(pixels,size,words,OUT/f'effect_{n}.png')
    bound_frames[str(n)]={'file':f'effect_{n}.png','sha256':file_hash(OUT/f'effect_{n}.png')}
evidence=ROOT/'work/ver_buki_riko/burst_layers/20261025T124957930178Z/vram_08.bin'
recipe={'kind':'us_rakuhouha_embedded_body_v1','source_texture_sha256':sha(texture),'parts_sha256':sha(parts),
    'palette_file':'palette.bin','palette_sha256':sha(pal),'palette_evidence_file':os.path.relpath(evidence,OUT),
    'palette_evidence_sha256':file_hash(evidence),'frames':bound_frames,'modified_texture_sha256':sha(new_texture)}
(OUT/'static_effects.json').write_text(json.dumps(recipe,indent=2)+'\n','utf8')
final,check=apply_static_set(arc,OUT/'static_effects.json')
assert final==replace_entry(arc,0x10206,new_texture)
(OUT/'PL01_U.ARC').write_bytes(final)
board=Image.new('RGB',(960,720),'#28323b');draw=ImageDraw.Draw(board)
from scripts.overhaul_sprites_audit import rgba
for column,(n,pair) in enumerate(previews.items()):
    for row,a in enumerate(pair):
        pic=rgba(a,words).resize((a.shape[1]*5,a.shape[0]*5),Image.Resampling.NEAREST)
        xy=(column*480+(480-pic.width)//2,row*360+25)
        board.paste(pic,xy,pic);draw.text((column*480+5,row*360+5),f'{n} '+('previous' if row==0 else 'new body'),fill='white')
board.save(OUT/'effect_comparison.png')
report={'source_arc':str(P.relative_to(ROOT)),'source_arc_sha256':sha(arc),'resource':str((OUT/'PL01_U.ARC').relative_to(ROOT)),
    'after_sha256':sha(final),'new_main_refs':[182,184,185],'main_cumulative_ref_count':80,'static_refs':[23,24],
    'old_effect_reconstruction':proof,'static_apply_checks':check,'other_entries_exact':True,
    'ready_for_disc_after_independent_review':True,'gameplay_runtime_verified':False}
(OUT/'proposal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'sha256':sha(final),'static_changed':users,'proof':proof}))
