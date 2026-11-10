"""낙봉파 돔의 제로 잔상만 린 몸체로 대체한다. 투사체/파츠/CLUT 보존."""
import json,os,struct
import numpy as np
from PIL import Image,ImageDraw
from scripts.prepare_rin_specials import ROOT,OUT
from scripts.build_rin_idle import entry,sha
from scripts.extract_zero import save_image
from scripts.project import digest
from scripts.assemble_rin_special_frames import world
from scripts.rakuhouha_static import apply_static_set
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_hurt_launch import compose_launch
from src.psx_static_effect import compose_static,patch_static

EVIDENCE=ROOT/'work/ver_rin_nana/live_poc/20261028T232731482621Z/vram.bin'

def prepare(arc,worlds):
    folder=OUT/'static_burst';folder.mkdir(exist_ok=True);_,texture=entry(arc,0x10206);_,parts=entry(arc,3)
    palette=EVIDENCE.read_bytes()[480*2048+96:480*2048+128];words=struct.unpack('<16H',palette);(folder/'palette.bin').write_bytes(palette)
    original=(ROOT/'work/ver_rin_nana/zero_extract/20261028T080358573477Z/original.arc').read_bytes();_,g=entry(original,2);_,op=entry(original,3)
    f=graphics_bank(g,1)['frames'][182];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;pic=compose_launch(raw,f['tile_count'],composition_frame(op,5,182));zero=np.roll(world(pic[:2],pic[2]),-1,axis=0)
    # Dark navy -> dark cyan silhouette, white cloth -> bright flash.
    remaps={23:[0,9,9,8,9,8,7,8,7,6,6,5,7,6,5,5],24:[0,15,15,14,15,14,12,14,12,11,10,5,12,10,5,5]}
    frames={};records={};comps={};masks={}
    for n,body in ((23,185),(24,182)):
        comp=composition_frame(parts,6,n);comps[n]=comp;data,size,b,prov=compose_static(texture,comp);a=np.frombuffer(data,np.uint8).reshape(size[1],size[0]);out=a.copy()
        old=(zero[128+b[1]:128+b[3],128+b[0]:128+b[2]]>0)&(a!=0);old[:max(0,-17-b[1])]=False
        if n==23 and np.any(np.isin(a,[6,7,8,9])&~old):raise ValueError('Uncovered original body tint')
        counts={}
        for locs in prov:
            for loc in locs:counts[loc]=counts.get(loc,0)+1
        unique=np.array([len(q)==1 and counts[q[0]]==1 for q in prov]).reshape(a.shape)
        if np.any(old&~unique):raise ValueError('Old body shares reflected dome tiles')
        for yy,xx in zip(*np.nonzero(old)):
            mirror=-12-(xx+b[0])-b[0]
            if 0<=mirror<size[0] and not old[yy,mirror] and a[yy,mirror]:value=a[yy,mirror]
            else:
                available=np.flatnonzero((~old[yy])&(a[yy]!=0))
                if not len(available):out[yy,xx]=0;continue
                closest=available[np.argsort(abs(available-xx),kind='stable')[:2]];value=a[yy,closest[0]]
                if n==24 and 13 in a[yy,available]:value=13
            out[yy,xx]=value
        rin=worlds[1][body][128+b[1]:128+b[3],128+b[0]:128+b[2]];overlay=(rin>0)&(a>0)&unique;remap=np.array(remaps[n],np.uint8);out[overlay]=remap[rin[overlay]]
        if not np.array_equal(out[~(old|overlay)],a[~(old|overlay)]):raise ValueError('Dome outside body changed')
        if not np.array_equal((out==0)[~old],(a==0)[~old]):raise ValueError('Dome transparency changed')
        frames[n]=(out.tobytes(),size);save_image(data,size,words,folder/f'before_{n}.png');save_image(out.tobytes(),size,words,folder/f'effect_{n}.png');masks[str(n)]=old|overlay
        records[str(n)]={'file':f'effect_{n}.png','sha256':digest(folder/f'effect_{n}.png'),'bounds':b,'body_source':body,'old_body_mask_pixels':int(old.sum()),'rin_tint_pixels':int(overlay.sum()),'body_world_sha256':sha(worlds[1][body].tobytes()),'tint_map':remaps[n]}
    changed=patch_static(texture,comps,frames)
    recipe={'kind':'us_rakuhouha_embedded_body_v1','project':'ver_rin_nana','source_texture_sha256':sha(texture),'parts_sha256':sha(parts),'palette_file':'palette.bin','palette_sha256':sha(palette),'palette_evidence_file':os.path.relpath(EVIDENCE,folder),'palette_evidence_sha256':digest(EVIDENCE),'frames':records,'modified_texture_sha256':sha(changed),'original_alpha_outside_old_body_preserved':True}
    path=folder/'static_effects.json';path.write_text(json.dumps(recipe,indent=2)+'\n','utf-8');np.savez(folder/'edit_masks.npz',**masks)
    candidate,report=apply_static_set(arc,path,project='ver_rin_nana')
    board=Image.new('RGB',(800,700),(35,38,48));d=ImageDraw.Draw(board)
    for i,n in enumerate((23,24)):
        for j,prefix in enumerate(('before','effect')):
            im=Image.open(folder/f'{prefix}_{n}.png').convert('RGBA');im=im.resize((im.width*5,im.height*5),Image.Resampling.NEAREST);xy=(i*400,j*350);board.paste(im,(xy[0],xy[1]+25),im);d.text(xy,f'{prefix} {n}',fill='white')
    board.save(folder/'review.png');return candidate,report
