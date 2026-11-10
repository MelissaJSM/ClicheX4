"""리코 특수14 원화/파생/공유 검기 타일을 제작 함수 없이 독립 재구성한다."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;W=H.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
sha=lambda b:hashlib.sha256(b).hexdigest()
P=W/'riko/prepared_special_clothes_v1';p=json.loads((P/'proposal.json').read_text('utf8'))
old=(ROOT/p['source_arc']).read_bytes();new=(ROOT/p['resource']).read_bytes()
assert sha(old)==p['source_arc_sha256']=='93844db97721cc95c89ece5a81eb48d9135f1e0f2c5aafb172d2890b11bff1b5'
assert sha(new)==p['after_sha256']=='03fa9ef5b662a71963f1b4e2be5a00fb7f18202e834e33f595a2b6b672c1d6a3'
D=W/'riko/special_clothes13';info=json.loads((D/'inputs.json').read_text('utf8'));reg=json.loads((D/'registered01/registration.json').read_text('utf8'))
assert info['sha256']==reg['source_sha256']==sha(old)
colors=np.array([[(v>>s&31)*255//31 for s in(0,5,10)]for v in struct.unpack_from('<16H',entry(old,9))],np.int32)
im=Image.open(D/'generated.png').convert('RGBA');assert sha((D/'generated.png').read_bytes())==reg['generated_sha256']=='8a07f057fcd45f3698bd546a3cfd1b168c9d1abc3ca27c5197db2c3cfa922234'
cw,ch=info['native_cell'];gx,gy=info['grid'];nw=cw*gx;scale=im.width/nw;nh=round(im.height/scale)
assert[nw,nh]==reg['native_canvas']and list(im.size)==reg['generated_dimensions']and scale==reg['uniform_source_scale']
pix=np.array(im.resize((nw,nh),Image.Resampling.NEAREST));q=(1+((pix[:,:,:3].astype(np.int32)[:,:,None,:]-colors[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);q[pix[:,:,3]<128]=0
idx=np.zeros((max(nh,ch*gy),nw),np.uint8);idx[:nh]=q
rects={50:(148,131,171,150),57:(148,131,171,150),108:(132,144,155,163),128:(133,144,156,163)}
keys={};sources=[];headmasks={}
for r in reg['frames']:
    n=r['ref'];spec=next(v for v in info['frames']if v['ref']==n);i=spec['cell'];previous=render(old,1,5,n)[0]
    source=np.zeros_like(previous);xb,yb=info['crop'][:2];source[yb:yb+ch,xb:xb+cw]=idx[i//gx*ch:(i//gx+1)*ch,i%gx*cw:(i%gx+1)*cw]
    x0,y0,x1,y1=rects[n];head=previous[y0:y1,x0:x1];green=np.isin(head,[4,8,14]);options=[]
    for dy in range(-8,9):
        for dx in range(-8,9):
            a=source[y0-dy:y1-dy,x0-dx:x1-dx];error=np.count_nonzero(a[green]!=head[green])+np.count_nonzero(np.isin(a,[4,8,14])&~green)
            options.append((int(error),abs(dx)+abs(dy),dx,dy))
    _,_,dx,dy=min(options);assert[dx,dy]==r['generated_translation']and list(rects[n])==r['head_rect']
    authored=np.zeros_like(previous);yy,xx=np.nonzero(source);authored[yy+dy,xx+dx]=source[yy,xx]
    assert np.array_equal(authored,np.array(Image.open(D/'registered01'/f'b1_{n:03}_authored.png')))
    mask=np.zeros_like(previous,bool)
    for y,row in enumerate(head):
        xs=np.flatnonzero(row)
        if len(xs):mask[y0+y,x0+xs.min():x0+xs.max()+1]=True
    assert int(mask.sum())==r['head_mask_pixels']and np.array_equal(mask,np.array(Image.open(D/'registered01'/f'b1_{n:03}_head_mask.png'))>0)
    win=np.zeros_like(mask);win[y0-2:y1+2,x0-2:x1+2]=True;result=authored.copy();result[win&np.isin(authored,[4,8,14])&~mask]=0;result[mask]=previous[mask]
    contact=np.zeros_like(mask)
    if n in(108,128):contact[156:165,80:127]=True
    result[contact]=previous[contact]
    assert int(contact.sum())==r['contact_mask_pixels']and np.array_equal(contact,np.array(Image.open(D/'registered01'/f'b1_{n:03}_contact_mask.png'))>0)
    path=ROOT/r['target'];assert sha(path.read_bytes())==r['target_sha256']and np.array_equal(result,np.array(Image.open(path)))
    keys[n]=result;headmasks[n]=mask;sources.append({'ref':n,'translation':[dx,dy],'head_pixels':int(mask.sum()),'contact_pixels':int(contact.sum()),'source_registration_exact':True,'hand_contact_exact':r['original_weapon_contact_exact']})
target_refs=[50,51,53,57,108,110,112,114,116,119,122,125,128,129];oldframes={n:render(old,1,5,n)[0]for n in target_refs}
for n in(108,128):
    legs=keys[n][173:].copy();keys[n][173:]=0;keys[n][172:383]=legs
    assert np.nonzero(keys[n])[0].max()==np.nonzero(oldframes[n])[0].max()==183
assert np.array_equal(oldframes[50][164:],oldframes[57][164:]);keys[57][164:]=keys[50][164:]
targets={50:keys[50].copy(),57:keys[57].copy(),128:keys[128].copy()};protected_regions={}
hand=np.zeros((384,384),bool);hand[140:154,145:159]=True
for n in(51,53):
    assert np.array_equal(oldframes[n][~hand],oldframes[50][~hand]);t=keys[50].copy();t[hand]=oldframes[n][hand];targets[n]=t;protected_regions[n]=hand
for n in(108,110,112,114,116,119,122,125):
    dx=-1 if n==110 else 0;assert not oldframes[108][:,0].any()and not keys[108][:,0].any()
    original=np.roll(oldframes[108],dx,axis=1);t=np.roll(keys[108],dx,axis=1)
    mask=np.zeros_like(hand);mask[147:165,166+dx:186+dx]=True;mask[156:165,80:127+dx]=True
    assert np.array_equal(original[~mask],oldframes[n][~mask]);t[mask]=oldframes[n][mask];targets[n]=t;protected_regions[n]=mask
assert np.array_equal(oldframes[128],oldframes[129]);targets[129]=targets[128].copy()
for r in p['registration']['frames']:
    path=ROOT/r['target'];assert sha(path.read_bytes())==r['target_sha256']and np.array_equal(targets[r['ref']],np.array(Image.open(path)))
assert set(p['target_references'])=={f'b1_{n:03}'for n in targets}
assert len(old)==len(new)and[(e['type'],e['offset'],e['size'])for e in psx_arc(old)]==[(e['type'],e['offset'],e['size'])for e in psx_arc(new)]
other_entries=0
for e in psx_arc(old):
    if int(e['type'],16)not in(2,3):assert old[e['offset']:e['offset']+e['size']]==new[e['offset']:e['offset']+e['size']];other_entries+=1
g,ng,c,nc=entry(old,2),entry(new,2),entry(old,3),entry(new,3)
assert bank_offsets(g)==bank_offsets(ng)and bank_offsets(c)==bank_offsets(nc)
assert g[:bank_offsets(g)[1]]==ng[:bank_offsets(ng)[1]]
semantic=lambda cp:[(r['flags'],r['tile'],r['x'],r['y'])for r in cp['parts']]
support={int(s.split('_')[1])for s in p['shared_support_refs']};assert len(support)==16
counts={'raw':0,'non_target_nonshared_raw':0,'display':0,'non_target_display':0,'target_display':0,'partial_raw_parts_only':0,'gpu_parts':0,'new_boundary_alpha':0,'protected_shared_tile_instances':0};shared_rows=[];changes=[]
for b in(0,1):
    bb,nb=graphics_bank(g,b),graphics_bank(ng,b);assert len(bb['frames'])==len(nb['frames'])
    for f,z in zip(bb['frames'],nb['frames']):
        n=f['index'];counts['raw']+=1;target=b==1 and n in targets;shared=b==1 and n in support
        assert f['tile_count']==z['tile_count']<=32
        raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,z['offset'],z['limit'],z['tile_count']*128).data
        cp,np_=composition_frame(c,b*5,n),composition_frame(nc,b*5,n)
        if not target and not shared:assert raw==nr;counts['non_target_nonshared_raw']+=1
        if not target:assert semantic(cp)==semantic(np_)
        if b==1 and n in range(42,50):counts['partial_raw_parts_only']+=1;continue
        actual=render(new,b,b*5,n)[0];before=render(old,b,b*5,n)[0]
        assert np.array_equal(actual,targets[n]if target else before),(b,n,'display');counts['display']+=1
        if not target:counts['non_target_display']+=1
        else:
            counts['target_display']+=1
            if n in protected_regions:assert np.array_equal(actual[protected_regions[n]],before[protected_regions[n]])
            changes.append({'ref':n,'changed_pixels':int(np.count_nonzero(actual!=before))})
        if not target and not shared:continue
        ta=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);tb=np.frombuffer(indexed_atlas(nr,z['tile_count'])[0],np.uint8).reshape(-1,256)
        if shared:
            tiles=sorted({r['tile']for r in cp['parts']})
            for t in tiles:
                x,y=t%16*16,t//16*16;assert np.array_equal(ta[y:y+16,x:x+16],tb[y:y+16,x:x+16]),(n,t,'effect raw tile')
                counts['protected_shared_tile_instances']+=1
            shared_rows.append({'ref':n,'read_tiles':tiles,'used_raw_tiles_exact':True,'display_exact':True,'parts_exact':True})
        for r in np_['parts']:
            t=r['tile'];x,y=t%16*16,t//16*16
            if t%16==0:assert not np.any((ta[y:y+16,x]==0)&(tb[y:y+16,x]>0))
            if r['flip_y']and t//16%16==0:assert not np.any((ta[y,x:x+16]==0)&(tb[y,x:x+16]>0))
            counts['gpu_parts']+=1
assert counts['raw']==444 and counts['non_target_nonshared_raw']==414 and counts['display']==436 and counts['non_target_display']==422
all_parts=0;changed_parts=[]
for b in range(len(bank_offsets(c))):
    count=composition_frame(c,b,0)['bank_frame_count'];assert count==composition_frame(nc,b,0)['bank_frame_count']
    for n in range(count):
        cp,np_=composition_frame(c,b,n),composition_frame(nc,b,n)
        if semantic(cp)!=semantic(np_):assert b==5 and n in targets;changed_parts.append(n)
        else:all_parts+=1
assert changed_parts==[108,110,112,114,116,119,122,125,128,129]
bank=graphics_bank(ng,1);assert len({bank['frames'][n]['offset']for n in(128,129,130,131)})==1
protected=set().union(*[set(r['tile']for r in composition_frame(c,5,n)['parts'])for n in(130,131)])
private=set(range(24))-protected;assert private=={2,3,4,6,7,8,9,10,11,12,15}
for n in(128,129):
    parts=composition_frame(nc,5,n)['parts'];assert len(parts)==10 and {q['tile']for q in parts}<=private
assert semantic(composition_frame(nc,5,128))==semantic(composition_frame(nc,5,129))
recipe=json.loads((P/'static_effects.json').read_text('utf8'));previous_recipe=json.loads((ROOT/p['source_arc']).with_name('static_effects.json').read_text('utf8'))
assert recipe['parts_sha256']==sha(nc)and{k:v for k,v in recipe.items()if k!='parts_sha256'}=={k:v for k,v in previous_recipe.items()if k!='parts_sha256'}
report={'passed':True,'parent_sha256':sha(old),'candidate_sha256':sha(new),'proposal_sha256':sha((P/'proposal.json').read_bytes()),'source_art_sha256':sha((D/'generated.png').read_bytes()),'authored_pose_count':4,'source_reconstruction':sources,'counts':counts,'changes':changes,'protected_shared_effect_tiles':shared_rows,'shared128_129':{'same_new_body_exact':True,'same_original_body_exact':True,'same_stream_all_four_refs':True,'private_tiles':sorted(private),'protected130_131_tiles':sorted(protected),'body_parts':10,'art_pixels_omitted':0},'all_other_composition_refs_exact':all_parts,'changed_composition_refs':changed_parts,'bank0_graphics_bytes_exact':True,'other_entries_exact':other_entries,'palette_audio_timing_exact':True,'static_recipe_sha256':sha((P/'static_effects.json').read_bytes()),'static_only_parts_hash_rebound':True,'producer_or_packer_called':False,'actual_view_image_files':[],'visual_notes':[],'limitations':['50/57의 원손 위치에 고정한 마스크는 없으며,108/128의 검 연결부는 원래 구역 보존을 확인했다.','원시 공유 검기 타일과 합성 표시를 모두 확인했으나 실제 게임의 검기 생성·판정·소리를 실행하지는 않았다.','8개 부분VRAM참조42..49는 원시/조립 보존만 확인했다.'],'runtime_verified':False}
report['actual_view_image_files']=[str((P/f'{mode}_readback_{i:02}.png').relative_to(ROOT))for mode in('normal','black')for i in range(4)]
report['visual_notes']=['일반·블랙14참조 재독출8시트를 실제로 열람했다. 올려친50류와 낮게 찌르는108류를 정상 포즈 차이로 구분했다.','새 칼라·어깨·허리·부츠 명암이 대기와 이어지고,108류는 몸의 디테일을 보완하면서 원 검 연결부와 망토 끝이 같은 원점에 남는다.','128/129는 동일 몸체 표시를 유지하며 검기130/131이 사용하는 타일을 원시 바이트까지 보존한다.','등록된 새 목표와 최종 표시가 모두 같으므로 저장 공간을 맞추기 위한 도트 삭제·축소는 검출되지 않았다.']
O=H/'riko_special_independent';O.mkdir(exist_ok=True);(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'counts':counts,'report':str(O/'verification.json')}))
