"""리코 등장·승리11: 원화9와 native 섬광2를 독립 재구성한다."""
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
P=W/'riko/prepared_ceremony_clothes_v2';p=json.loads((P/'proposal.json').read_text('utf8'))
old=(ROOT/p['source_arc']).read_bytes();new=(ROOT/p['resource']).read_bytes()
assert sha(old)==p['source_arc_sha256']=='dd61d2f1b77cab1c43256dd6e2553f631067100338352c86aaea1d5d41eddec7'
assert sha(new)==p['after_sha256']=='0de65ee0ee43f9c2713af4ce372023325cc2389bd42664f460ff93d2efd2a7d0'
D=W/'riko/ceremony_clothes16'
colors=np.array([[(v>>s&31)*255//31 for s in(0,5,10)]for v in struct.unpack_from('<16H',entry(old,9))],np.int32)
HEAD={(0,249):(146,144,169,163),(0,250):(152,134,175,153),(0,251):(151,134,174,153),
      (0,252):(150,138,173,157),(0,253):(148,138,171,157),(1,2):(145,133,168,152),
      (1,3):(144,134,167,153),(1,4):(145,134,168,153),(1,6):(144,134,167,153)}
targets={};sources=[]
for pn in range(1,6):
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
        x0,y0,x1,y1=HEAD[key];head=previous[y0:y1,x0:x1];green=np.isin(head,[4,8,14]);options=[]
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
def flash(a,ref):
    mask=a>0;radius=1 if ref==7 else 2;expanded=np.zeros_like(mask)
    yy,xx=np.nonzero(mask)
    for dy in range(-radius,radius+1):
        for dx in range(-radius,radius+1):
            if abs(dx)+abs(dy)>radius:continue
            assert ((xx+dx>=0)&(xx+dx<384)&(yy+dy>=0)&(yy+dy<384)).all()
            expanded[yy+dy,xx+dx]=True
    q=np.where(expanded,15 if ref==7 else 12,0).astype(np.uint8)
    pale=np.array([0,12,12,12,15,15,12,15,15,15,12,12,15,12,15,15],np.uint8)
    q[mask]=a[mask] if ref==7 else pale[a[mask]]
    return q
old3=render(old,1,5,3)[0]
for n in(7,8):
    assert np.array_equal(flash(old3,n),render(old,1,5,n)[0]),'Original flash rule not reproduced'
    targets[1,n]=flash(targets[1,3],n)
for r in p['registration']['frames']:
    key=r['bank'],r['ref'];rp=ROOT/r['target'];assert sha(rp.read_bytes())==r['target_sha256'] and np.array_equal(targets[key],np.array(Image.open(rp)))
assert set(p['target_references'])=={f'b{b}_{n:03}'for b,n in targets}
support={(1,n)for n in(0,1,5,9)};assert set(p['shared_support_refs'])=={f'b{b}_{n:03}'for b,n in support}
assert len(old)==len(new) and [(e['type'],e['offset'],e['size'])for e in psx_arc(old)]==[(e['type'],e['offset'],e['size'])for e in psx_arc(new)]
for e in psx_arc(old):
    if int(e['type'],16)!=2:assert old[e['offset']:e['offset']+e['size']]==new[e['offset']:e['offset']+e['size']]
g,ng,c,nc=entry(old,2),entry(new,2),entry(old,3),entry(new,3);assert c==nc and bank_offsets(g)==bank_offsets(ng)
counts={'raw':0,'non_target_raw':0,'display':0,'non_target_display':0,'target_display':0,'partial_raw_parts_only':0,'gpu_parts':0,'support_tile_instances':0}
changes=[];support_rows=[]
for b in (0,1):
    bb,nn=graphics_bank(g,b),graphics_bank(ng,b);assert len(bb['frames'])==len(nn['frames'])
    for f,z in zip(bb['frames'],nn['frames']):
        n=f['index'];key=b,n;selected=key in targets;is_support=key in support;counts['raw']+=1;assert f['tile_count']==z['tile_count']<=32
        raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,z['offset'],z['limit'],z['tile_count']*128).data
        if not selected and not is_support:assert raw==nr;counts['non_target_raw']+=1
        cp=composition_frame(c,b*5,n)
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
assert counts['raw']==444 and counts['non_target_raw']==429 and counts['display']==436 and counts['non_target_display']==425 and counts['target_display']==11
sp=P/'static_effects.json';prior=(ROOT/p['source_arc']).with_name('static_effects.json');assert sp.read_bytes()==prior.read_bytes()
report={'passed':True,'parent_sha256':sha(old),'candidate_sha256':sha(new),'proposal_sha256':sha((P/'proposal.json').read_bytes()),
        'source_art9_independently_reconstructed':sources,'native_flash_derivations':[{'ref':7,'radius':1,'original_reproduced_exact':True},{'ref':8,'radius':2,'original_reproduced_exact':True}],
        'counts':counts,'changes':changes,'support_original_consumed_tile_windows':support_rows,
        'all_composition_bytes_exact':True,'other_entries_exact_including_palette_audio_timing':True,'fixed_bank_boundaries_exact':True,
        'static_recipe_bytes_exact':True,'static_recipe_sha256':sha(sp.read_bytes()),'producer_packer_or_generation_called':False,
        'runtime_verified':False,'visual_review_pending':False,'frozen':True,
        'actual_viewed_packed_sheets':[{'path':str((P/f'{mode}_readback_{i:02}.png').relative_to(ROOT)),
                                      'sha256':sha((P/f'{mode}_readback_{i:02}.png').read_bytes())}
                                     for mode in ('normal','black')for i in range(3)],
        'visual_notes':['일반/블랙 ARC 재독출6장을 실제 열람했다.249의 숙임과250~253의 벌린 다리는 원자세이며 상의·소매·부츠 명암이 대기와 이어진다.',
                        '2/3/4/6의 측면 몸체는 원래보다 허리장식·옷단·부츠 분할이 읽히며 목/허리의 새로운 빈틈은 보이지 않는다.',
                        '7/8은 새3의 형태를 정확히 따라가는 섬광이며,밝은 단색 효과를 의상 상세 부족으로 오판하지 않았다.'],
        'limitations':['부분 VRAM bank1 42..49는 원시/조립 보존만 확인했다. 미완성 독립 표시를 새 몸체로 채우지 않는다.',
                      '손 접점은 이 원화 묶음에서 원래 픽셀 동일을 보장한 것으로 보고하지 않는다.',
                      '원래 MIPS/GPU 실행과 실제 게임은 별도 루트 검사다.']}
O=H/'riko_ceremony_independent';O.mkdir(exist_ok=True);(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'counts':counts,'support':support_rows,'report':str(O/'verification.json')}))
