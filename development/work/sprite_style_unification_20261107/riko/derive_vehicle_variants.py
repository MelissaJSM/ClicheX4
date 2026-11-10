"""원래 몸체가 같은 체이서 포즈에 원래 망토 변형·정수 원점차만 연결한다."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
W=ROOT/'work/sprite_style_unification_20261107';P=W/'riko/prepared_jump_clothes_v1/PL01_U.ARC';OLD=W/'riko/prepared_head_spaces_v1/PL01_U.ARC'
D=W/'riko/vehicle_clothes09';OUT=D/'variants02';OUT.mkdir(exist_ok=False)
sha=lambda b:hashlib.sha256(b).hexdigest();arc=P.read_bytes();old=OLD.read_bytes()
assert sha(arc)=='95867666de2ab6a0a3712de5b047a0c6f44fb827d74cc6b2d873f854739b84e9'
assert sha(old)=='488b679ed027fd8916e0f48716c9e3fa65d03ff42d4ac21d38dffb6ed0a7edaf'
def shift(a,dy):
    out=np.zeros_like(a);y,x=np.nonzero(a);assert min(y+dy)>=0 and max(y+dy)<384;out[y+dy,x]=a[y,x];return out
def selected_parts(data,n,body=True):
    g,c=entry(data,2),entry(data,3);f=graphics_bank(g,1)['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;cp=composition_frame(c,5,n)
    cp['parts']=[p for p in cp['parts']if (p['tile'] in {12,13,14,15,28,29,30,31})==body]
    pix,size,bb,_=compose_indices(raw,f['tile_count'],cp);small=np.frombuffer(pix,np.uint8).reshape(size[1],size[0]);out=np.zeros((384,384),np.uint8);y,x=np.nonzero(small);out[y+160+bb[1],x+160+bb[0]]=small[y,x];return out
masters={17:render(arc,1,5,17)[0]};reg=json.loads((D/'registered01/registration.json').read_text('utf8'));assert reg['source_sha256']==sha(arc)
for r in reg['frames']:
    p=ROOT/r['target'];assert sha(p.read_bytes())==r['target_sha256'];masters[r['ref']]=np.array(Image.open(p))
targets={};records=[]
for master,start,end in [(17,14,22),(25,22,30),(33,30,38),(41,38,42)]:
    source=old if master==17 else arc;reference=render(source,1,5,master)[0];body=selected_parts(source,master)
    # The first probe mixed old and new cape pixels and left cyan flecks.
    # Reassemble the original independent cape layer under the refined body.
    cape_union=np.zeros_like(body,bool)
    for n in range(start,start+4):cape_union|=selected_parts(source,n,False)>0
    cy,cx=np.nonzero(cape_union);region=np.zeros_like(body,bool)
    region[cy.min()-2:cy.max()+3,cx.min()-2:cx.max()+3]=True
    clear_mask=region&(body==0)
    new_body=masters[master].copy();new_body[clear_mask]=0
    for n in range(start,end):
        if n in [17,20]:continue
        dy={4:1,5:2,6:1,7:-1}.get(n-start,0)
        actual=render(source,1,5,n)[0];shifted_reference=shift(reference,dy);shifted_body=shift(body,dy)
        assert np.array_equal(selected_parts(source,n),shifted_body),(n,'Original body differs')
        delta=actual!=shifted_reference
        assert not np.any(delta&(shifted_body>0)),(n,'Cape mask includes body')
        authored=shift(new_body,dy);cape=selected_parts(source,n,False);out=cape.copy();out[authored>0]=authored[authored>0]
        assert np.array_equal(out[authored>0],authored[authored>0])
        Image.fromarray(out).save(OUT/f'b1_{n:03}_indices.png');Image.fromarray(delta.astype('uint8')*255).save(OUT/f'b1_{n:03}_cape_delta.png');targets[n]=out
        records.append(dict(bank=1,ref=n,master=master,translation=[0,dy],original_body_parts_exact=True,cape_changed_cells=int(delta.sum()),original_cape_composited_behind_new_body=True,new_body_preserved_exact=True,body_registration_clear_mask_bounds=[int(cx.min()-2),int(cy.min()-2),int(cx.max()+3),int(cy.max()+3)],target=str((OUT/f'b1_{n:03}_indices.png').relative_to(ROOT)),target_sha256=sha((OUT/f'b1_{n:03}_indices.png').read_bytes())))
assert len(targets)==26
for label,row in [('normal',0),('black',13)]:
    pal=struct.unpack_from('<16H',entry(arc,9),row*32)
    for page,start in enumerate(range(0,26,7)):
        subset=list(targets.items())[start:start+7];sheet=Image.new('RGB',(288*4,260*len(subset)),'#64717b');draw=ImageDraw.Draw(sheet)
        for iy,(n,out)in enumerate(subset):
            master=next(r['master']for r in records if r['ref']==n)
            for ix,(title,a)in enumerate([('idle',render(arc,0,0,147)[0]),('old',render(arc,1,5,n)[0]),('new key',masters[master]),('variant',out)]):
                im=rgba(a,pal).crop((112,112,208,192)).resize((288,240),Image.Resampling.NEAREST);sheet.paste(im,(ix*288,iy*260+20),im);draw.text((ix*288+3,iy*260+3),f'{n} {title}',fill='white')
        sheet.save(OUT/f'{label}_comparison_{page}.png')
(OUT/'registration.json').write_text(json.dumps(dict(source_arc=str(P.relative_to(ROOT)),source_sha256=sha(arc),original_pre_ceremony_sha256=sha(old),new_key_source=str(D/'registered01/registration.json'),unchanged_refs=[17,20],frames=records,candidate_only=True,runtime_verified=False),indent=2)+'\n','utf8');print('26 variants prepared')
