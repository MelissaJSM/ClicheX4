"""리코 회전8: 원화와 원래 회전 머리·검기를 독립 확인한다."""
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
P=W/'riko/prepared_spin_clothes_v1';p=json.loads((P/'proposal.json').read_text('utf8'))
old=(ROOT/p['source_arc']).read_bytes();new=(ROOT/p['resource']).read_bytes()
assert sha(old)==p['source_arc_sha256']=='0de65ee0ee43f9c2713af4ce372023325cc2389bd42664f460ff93d2efd2a7d0'
assert sha(new)==p['after_sha256']=='c68ef84d524a16062937359c52f9d640213b250ea2b679a673046f977d997e42'
D=W/'riko/spin_clothes17'
colors=np.array([[(v>>s&31)*255//31 for s in(0,5,10)]for v in struct.unpack_from('<16H',entry(old,9))],np.int32)
HEAD={};rotated={};original=render(old,1,5,161)[0];headbase=np.zeros_like(original);headbase[141:160,146:169]=original[141:160,146:169]
for j,n in enumerate(range(161,176,2)):
    q=np.array(Image.fromarray(headbase).rotate(j*45,Image.Resampling.NEAREST,center=(160.5,160)))
    assert np.array_equal(q,np.array(Image.open(D/f'head_{n:03}.png')))
    actual=render(old,1,5,n)[0];assert np.array_equal(q[q>0],actual[q>0])
    yy,xx=np.nonzero(q);HEAD[1,n]=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));rotated[n]=q
targets={};sources=[]
for pn in range(1,3):
    d=D/f'page{pn}';info=json.loads((d/'inputs.json').read_text('utf8'));reg=json.loads((d/'registered01/registration.json').read_text('utf8'))
    assert info['sha256']==reg['source_sha256']==sha(old)
    ip=d/'generated.png';im=Image.open(ip).convert('RGBA');assert sha(ip.read_bytes())==reg['generated_sha256']
    cw,ch=info['native_cell'];cols,rows=info['grid'];width=cw*cols;scale=im.width/width;nh=round(im.height/scale)
    assert [width,nh]==reg['native_canvas'] and list(im.size)==reg['generated_dimensions'] and scale==reg['uniform_source_scale'] and abs(nh-ch*rows)<=1
    px=np.array(im.resize((width,nh),Image.Resampling.NEAREST))
    ix=(1+((px[:,:,:3].astype(np.int32)[:,:,None,:]-colors[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);ix[px[:,:,3]<128]=0
    canvas=np.zeros((max(nh,ch*rows),width),np.uint8);canvas[:nh]=ix
    assert {(r['bank'],r['ref'])for r in reg['frames']}=={tuple(k)for k in info['apply_only_keys']}
    for r in reg['frames']:
        b,n=r['bank'],r['ref'];key=b,n;f=next(q for q in info['frames']if(q['bank'],q['ref'])==key);cy,cx=divmod(f['cell'],cols)
        previous=render(old,b,b*5,n)[0];generated=np.zeros_like(previous);xb,yb=info['crop'][:2]
        generated[yb:yb+ch,xb:xb+cw]=canvas[cy*ch:(cy+1)*ch,cx*cw:(cx+1)*cw]
        x0,y0,x1,y1=HEAD[key];head=rotated[n][y0:y1,x0:x1];green=np.isin(head,[4,8,14]);options=[]
        for dy in range(-8,9):
            for dx in range(-8,9):
                q=generated[y0-dy:y1-dy,x0-dx:x1-dx]
                score=int(np.count_nonzero(q[green]!=head[green])+np.count_nonzero(np.isin(q,[4,8,14])&~green));options.append((score,abs(dx)+abs(dy),dx,dy))
        score,_,dx,dy=min(options);assert [dx,dy]==r['generated_translation']
        authored=np.zeros_like(previous);yy,xx=np.nonzero(generated);assert ((xx+dx>=0)&(xx+dx<384)&(yy+dy>=0)&(yy+dy<384)).all();authored[yy+dy,xx+dx]=generated[yy,xx]
        stem=f'b{b}_{n:03}';assert np.array_equal(authored,np.array(Image.open(d/'registered01'/f'{stem}_authored.png')))
        mask=np.zeros_like(previous,bool)
        for y,line in enumerate(head):
            xs=np.flatnonzero(line)
            if len(xs):mask[y0+y,x0+xs.min():x0+xs.max()+1]=True
        result=authored.copy();window=np.zeros_like(mask);window[y0-2:y1+2,x0-2:x1+2]=True
        result[window&np.isin(authored,[4,8,14])&~mask]=0;result[mask]=previous[mask]
        assert int(mask.sum())==r['head_mask_pixels'] and np.array_equal(mask,np.array(Image.open(d/'registered01'/f'{stem}_head_mask.png'))>0)
        assert r['contact_mask_pixels']==0 and r['original_weapon_contact_exact']is None
        rp=ROOT/r['target'];assert sha(rp.read_bytes())==r['target_sha256'] and np.array_equal(result,np.array(Image.open(rp)))
        targets[key]=result;sources.append({'bank':b,'ref':n,'page':pn,'source_sha256':reg['generated_sha256'],'uniform_scale':scale,'translation':[dx,dy],'head_region_exact_pixels':int(mask.sum()),'hands_preservation_claimed':False})
assert set(targets)==set(HEAD)
for r in p['registration']['frames']:
    key=r['bank'],r['ref'];rp=ROOT/r['target'];assert sha(rp.read_bytes())==r['target_sha256'] and np.array_equal(targets[key],np.array(Image.open(rp)))
assert set(p['target_references'])=={f'b{b}_{n:03}'for b,n in targets}
support={(1,n)for n in range(162,177,2)};assert set(p['shared_support_refs'])=={f'b{b}_{n:03}'for b,n in support}
assert len(old)==len(new) and [(e['type'],e['offset'],e['size'])for e in psx_arc(old)]==[(e['type'],e['offset'],e['size'])for e in psx_arc(new)]
for e in psx_arc(old):
    if int(e['type'],16)not in(2,3):assert old[e['offset']:e['offset']+e['size']]==new[e['offset']:e['offset']+e['size']]
g,ng,c,nc=entry(old,2),entry(new,2),entry(old,3),entry(new,3);assert bank_offsets(c)==bank_offsets(nc) and bank_offsets(g)==bank_offsets(ng)
counts={'raw':0,'non_target_raw':0,'display':0,'non_target_display':0,'target_display':0,'partial_raw_parts_only':0,'gpu_parts':0,'support_tile_instances':0}
changes=[];support_rows=[]
for b in (0,1):
    bb,nn=graphics_bank(g,b),graphics_bank(ng,b);assert len(bb['frames'])==len(nn['frames'])
    for f,z in zip(bb['frames'],nn['frames']):
        n=f['index'];key=b,n;selected=key in targets;is_support=key in support;counts['raw']+=1;assert f['tile_count']==z['tile_count']<=32
        raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,z['offset'],z['limit'],z['tile_count']*128).data
        if not selected and not is_support:assert raw==nr;counts['non_target_raw']+=1
        cp=composition_frame(nc if selected else c,b*5,n)
        if is_support:
            oa=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);na=np.frombuffer(indexed_atlas(nr,z['tile_count'])[0],np.uint8).reshape(-1,256)
            for r in cp['parts']:
                t=r['tile'];tx,ty=t%16*16,t//16*16;assert np.array_equal(oa[ty:ty+16,tx:tx+16],na[ty:ty+16,tx:tx+16]),(key,t,'support used tile');counts['support_tile_instances']+=1
            support_rows.append({'bank':b,'ref':n,'whole_raw_equal':raw==nr,'all_used_tile_windows_exact':True})
        if b==1 and n in range(42,50):counts['partial_raw_parts_only']+=1;continue
        was=render(old,b,b*5,n)[0];actual=render(new,b,b*5,n)[0];assert np.array_equal(actual,targets[key]if selected else was),(key,'display');counts['display']+=1
        if not selected:counts['non_target_display']+=1;continue
        counts['target_display']+=1
        ta=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);tb=np.frombuffer(indexed_atlas(nr,z['tile_count'])[0],np.uint8).reshape(-1,256)
        for r in cp['parts']:
            t=r['tile'];x=t%16*16;y=t//16*16
            if t%16==0:assert not np.any((ta[y:y+16,x]==0)&(tb[y:y+16,x]>0))
            if r['flip_y']and t//16%16==0:assert not np.any((ta[y,x:x+16]==0)&(tb[y,x:x+16]>0))
            counts['gpu_parts']+=1
        changes.append({'bank':b,'ref':n,'changed_display_pixels':int(np.count_nonzero(was!=actual))})
assert counts['raw']==444 and counts['non_target_raw']==428 and counts['display']==436 and counts['non_target_display']==428 and counts['target_display']==8
changes_parts=[];semantic=lambda cp:[(r['flags'],r['tile'],r['x'],r['y'])for r in cp['parts']]
for b in range(len(bank_offsets(c))):
    count=composition_frame(c,b,0)['bank_frame_count'];assert count==composition_frame(nc,b,0)['bank_frame_count']
    for n in range(count):
        if semantic(composition_frame(c,b,n))!=semantic(composition_frame(nc,b,n)):
            assert b==5 and n==171;changes_parts.append([b,n])
assert changes_parts==[[5,171]]
assert g[bank_offsets(g)[0]:bank_offsets(g)[1]]==ng[bank_offsets(ng)[0]:bank_offsets(ng)[1]]
sp=P/'static_effects.json';prior=(ROOT/p['source_arc']).with_name('static_effects.json');rec=json.loads(sp.read_text('utf8'));before=json.loads(prior.read_text('utf8'))
assert rec['parts_sha256']==sha(nc) and {k:v for k,v in rec.items()if k!='parts_sha256'}=={k:v for k,v in before.items()if k!='parts_sha256'}
report={'passed':True,'parent_sha256':sha(old),'candidate_sha256':sha(new),'proposal_sha256':sha((P/'proposal.json').read_bytes()),'sources':sources,'counts':counts,'changes':changes,'support_tile_windows':support_rows,'original_eight_rotated_heads_exact':True,'rotation_center':[160.5,160],'rotation_degrees':[j*45 for j in range(8)],'source_alpha_cut':128,'registered_pixels_exact_to_independent_alpha128_reconstruction':True,'changed_composition_refs':changes_parts,'bank0_graphics_bytes_exact':True,'other_entries_exact':True,'static_recipe_only_parts_hash_rebound':True,'producer_packer_or_generation_called':False,'runtime_verified':False,'visual_review_pending':False,'frozen':True}
report['actual_viewed_packed_sheets']=[{'path':str((P/f'{mode}_readback_{i:02}.png').relative_to(ROOT)),'sha256':sha((P/f'{mode}_readback_{i:02}.png').read_bytes())}for mode in('normal','black')for i in range(2)]
report['visual_notes']=['일반/블랙 재독출4장을 실제 열람했다. 원래8각도와 머리 크기는 그대로이며 부츠·칼라·치마의 회색/남색 분할이 대기와 이어진다.','163/165/171의 뒤집힌 자세는 원래 회전이고 허리/목에 새로운 틈은 보이지 않는다. 배경 halo도 네이티브 표시에서 보이지 않는다.','원검기8은92개 소비 타일창 전체/좌표 보존이다. 실기 검기와의 동적 연결 및 원MIPS/GPU 검사는 별도 루트 근거다.']
report['limitations']=['부분 VRAM bank1 42..49는 원시와 조립 보존만 확인했다.','팔·검 접점 원픽셀 전체 동일을 주장하지 않는다.','현재 검사는 정적 그림·등록 재구성이며 실제 게임 영상이나 전체 미술 완료가 아니다.']
O=H/'riko_spin_independent';O.mkdir(exist_ok=True);(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'counts':counts,'report':str(O/'verification.json')}))
