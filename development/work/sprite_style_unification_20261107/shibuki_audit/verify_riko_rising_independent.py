"""리코 용염인15의 원화·파생·공유 지원 타일을 별도 읽기로 재구성한다."""
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
P=W/'riko/prepared_rising_clothes_v1';p=json.loads((P/'proposal.json').read_text('utf8'))
old=(ROOT/p['source_arc']).read_bytes();new=(ROOT/p['resource']).read_bytes()
assert sha(old)==p['source_arc_sha256']=='df73f6a50dc13c9b5c00b8cc60ab474e7b725011ea896f94712013f7fe411e7a'
assert sha(new)==p['after_sha256']=='dd61d2f1b77cab1c43256dd6e2553f631067100338352c86aaea1d5d41eddec7'
D=W/'riko/rising_clothes15';colors=np.array([[(v>>s&31)*255//31 for s in(0,5,10)]for v in struct.unpack_from('<16H',entry(old,9))],np.int32)
HEAD={133:(148,130,171,149),138:(147,145,170,164),146:(139,143,162,162),156:(138,137,161,156),158:(144,133,167,152)}
CONTACT={133:[(148,149,157,166)],138:[(145,162,154,172)],146:[(130,164,143,176)],156:[(161,120,169,134)],158:[(165,128,175,143)]}
keys={};heads={};sources=[]
for page_number in (2,3,4):
    d=D/f'page{page_number}';info=json.loads((d/'inputs.json').read_text('utf8'));reg=json.loads((d/'registered01/registration.json').read_text('utf8'))
    assert info['sha256']==reg['source_sha256']==sha(old)
    ip=d/'generated.png';im=Image.open(ip).convert('RGBA');assert sha(ip.read_bytes())==reg['generated_sha256']
    cw,ch=info['native_cell'];cols,rows=info['grid'];width=cw*cols;scale=im.width/width;nh=round(im.height/scale)
    assert [width,nh]==reg['native_canvas'] and list(im.size)==reg['generated_dimensions'] and scale==reg['uniform_source_scale'] and abs(nh-ch*rows)<=1
    px=np.array(im.resize((width,nh),Image.Resampling.NEAREST));idx=(1+((px[:,:,:3].astype(np.int32)[:,:,None,:]-colors[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);idx[px[:,:,3]<128]=0
    canvas=np.zeros((max(nh,ch*rows),width),np.uint8);canvas[:nh]=idx
    assert set(v['ref']for v in reg['frames'])==set(info['apply_only_refs'])
    for r in reg['frames']:
        n=r['ref'];f=next(v for v in info['frames']if v['ref']==n);cy,cx=divmod(f['cell'],cols)
        previous=render(old,1,5,n)[0];generated=np.zeros_like(previous);xbase,ybase=info['crop'][:2];generated[ybase:ybase+ch,xbase:xbase+cw]=canvas[cy*ch:(cy+1)*ch,cx*cw:(cx+1)*cw]
        x0,y0,x1,y1=HEAD[n];head=previous[y0:y1,x0:x1];green=np.isin(head,[4,8,14]);options=[]
        for dy in range(-8,9):
            for dx in range(-8,9):
                q=generated[y0-dy:y1-dy,x0-dx:x1-dx];score=int(np.count_nonzero(q[green]!=head[green])+np.count_nonzero(np.isin(q,[4,8,14])&~green));options.append((score,abs(dx)+abs(dy),dx,dy))
        score,_,dx,dy=min(options);assert [dx,dy]==r['generated_translation']
        authored=np.zeros_like(previous);yy,xx=np.nonzero(generated);assert ((xx+dx>=0)&(xx+dx<384)&(yy+dy>=0)&(yy+dy<384)).all();authored[yy+dy,xx+dx]=generated[yy,xx]
        assert np.array_equal(authored,np.array(Image.open(d/'registered01'/f'b1_{n:03}_authored.png')))
        m=np.zeros_like(previous,bool)
        for y,row in enumerate(head):
            xs=np.flatnonzero(row)
            if len(xs):m[y0+y,x0+xs.min():x0+xs.max()+1]=True
        result=authored.copy();window=np.zeros_like(m);window[y0-2:y1+2,x0-2:x1+2]=True;result[window&np.isin(authored,[4,8,14])&~m]=0;result[m]=previous[m]
        assert int(m.sum())==r['head_mask_pixels'] and np.array_equal(m,np.array(Image.open(d/'registered01'/f'b1_{n:03}_head_mask.png'))>0)
        rp=ROOT/r['target'];assert sha(rp.read_bytes())==r['target_sha256'] and np.array_equal(result,np.array(Image.open(rp)))
        assert r['contact_mask_pixels']==0 and r['original_weapon_contact_exact']is None
        for xa,ya,xb,yb in CONTACT[n]:result[ya:yb,xa:xb]=previous[ya:yb,xa:xb]
        keys[n]=result;heads[n]=m;sources.append({'ref':n,'page':page_number,'generated_sha256':reg['generated_sha256'],'fixed_scale':scale,'translation':[dx,dy],'head_preserved_pixels':int(m.sum()),'contact_rects':CONTACT[n]})
assert set(keys)==set(HEAD)
target={n:keys[n].copy()for n in(146,156,158)};oldrefs={n:render(old,1,5,n)[0]for n in list(range(133,145))+[146,156,158]};variants=[]
for n in range(133,138):
    m=np.zeros((384,384),bool);m[135:148,177:184]=True;assert np.array_equal(oldrefs[n][~m],oldrefs[133][~m]);q=keys[133].copy();q[m]=oldrefs[n][m];target[n]=q
    variants.append({'ref':n,'master':133,'original_cape_rect':[177,135,184,148],'exact':True})
for n in range(138,145):
    dx=0 if n==138 else -1 if n==144 else 1;m=np.zeros((384,384),bool);m[158:175,173+dx:184+dx]=True
    if n==144:m[159:172,144:156]=True
    assert np.array_equal(oldrefs[n][~m],np.roll(oldrefs[138],dx,axis=1)[~m]);q=np.roll(keys[138],dx,axis=1);q[m]=oldrefs[n][m];target[n]=q
    variants.append({'ref':n,'master':138,'translation':[dx,0],'original_cape_hand_exact':True})
for r in p['registration']['frames']:
    rp=ROOT/r['target'];assert sha(rp.read_bytes())==r['target_sha256'] and np.array_equal(target[r['ref']],np.array(Image.open(rp)))
assert set(p['target_references'])=={f'b1_{n:03}'for n in target}
support={145,147,157,159};assert set(p['shared_support_refs'])=={f'b1_{n:03}'for n in support}
assert len(old)==len(new) and [(e['type'],e['offset'],e['size'])for e in psx_arc(old)]==[(e['type'],e['offset'],e['size'])for e in psx_arc(new)]
others=0
for e in psx_arc(old):
    if int(e['type'],16)not in(2,3):assert old[e['offset']:e['offset']+e['size']]==new[e['offset']:e['offset']+e['size']];others+=1
g,ng,c,nc=entry(old,2),entry(new,2),entry(old,3),entry(new,3);assert bank_offsets(g)==bank_offsets(ng) and bank_offsets(c)==bank_offsets(nc)
assert g[bank_offsets(g)[0]:bank_offsets(g)[1]]==ng[bank_offsets(ng)[0]:bank_offsets(ng)[1]]
semantic=lambda cp:[(r['flags'],r['tile'],r['x'],r['y'])for r in cp['parts']]
counts={'raw':0,'non_target_raw':0,'display':0,'non_target_display':0,'target_display':0,'partial_raw_parts_only':0,'gpu_parts':0,'support_tile_instances':0}
changes=[]
for b in (0,1):
    bb,nn=graphics_bank(g,b),graphics_bank(ng,b);assert len(bb['frames'])==len(nn['frames'])
    for f,z in zip(bb['frames'],nn['frames']):
        n=f['index'];selected=b==1 and n in target;is_support=b==1 and n in support;counts['raw']+=1;assert f['tile_count']==z['tile_count']<=32
        raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,z['offset'],z['limit'],z['tile_count']*128).data
        cp,np_=composition_frame(c,b*5,n),composition_frame(nc,b*5,n)
        if not selected and not is_support:assert raw==nr and semantic(cp)==semantic(np_);counts['non_target_raw']+=1
        if is_support:
            assert semantic(cp)==semantic(np_)
            # Raw bytes are VRAM scanlines, NOT contiguous 128-byte tiles.
            # Compare the exact 16x16 atlas windows consumed by each part.
            oa=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256)
            na=np.frombuffer(indexed_atlas(nr,z['tile_count'])[0],np.uint8).reshape(-1,256)
            for r in cp['parts']:
                t=r['tile'];tx,ty=t%16*16,t//16*16;assert np.array_equal(oa[ty:ty+16,tx:tx+16],na[ty:ty+16,tx:tx+16]),(n,t,'support used tile');counts['support_tile_instances']+=1
        if b==1 and n in range(42,50):counts['partial_raw_parts_only']+=1;continue
        was=render(old,b,b*5,n)[0];actual=render(new,b,b*5,n)[0];assert np.array_equal(actual,target[n]if selected else was),(b,n,'display');counts['display']+=1
        if not selected:counts['non_target_display']+=1;continue
        counts['target_display']+=1
        ta=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);tb=np.frombuffer(indexed_atlas(nr,z['tile_count'])[0],np.uint8).reshape(-1,256)
        for r in np_['parts']:
            t=r['tile'];x=t%16*16;y=t//16*16
            if t%16==0:assert not np.any((ta[y:y+16,x]==0)&(tb[y:y+16,x]>0))
            if r['flip_y']and t//16%16==0:assert not np.any((ta[y,x:x+16]==0)&(tb[y,x:x+16]>0))
            counts['gpu_parts']+=1
        changes.append({'ref':n,'changed_display_pixels':int(np.count_nonzero(was!=actual))})
assert counts['raw']==444 and counts['non_target_raw']==425 and counts['display']==436 and counts['non_target_display']==421 and counts['target_display']==15
changed=[];kept=0
for b in range(len(bank_offsets(c))):
    count=composition_frame(c,b,0)['bank_frame_count'];assert count==composition_frame(nc,b,0)['bank_frame_count']
    for n in range(count):
        x,y=composition_frame(c,b,n),composition_frame(nc,b,n)
        if semantic(x)==semantic(y):kept+=1;continue
        assert b==5 and n==156;changed.append({'bank':b,'ref':n,'before':semantic(x),'after':semantic(y)})
assert len(changed)==1
report={'passed':True,'parent_sha256':sha(old),'candidate_sha256':sha(new),'proposal_sha256':sha((P/'proposal.json').read_bytes()),'raw_source_art_reconstructions':5,'selected_source_pages':[2,3,4],'rejected_page1_not_used':True,'sources':sources,'variant_derivations':variants,'counts':counts,'changes':changes,'non_target_composition_refs_exact':kept,'changed_compositions':changed,'other_entries_exact':others,'bank0_graphics_bytes_exact':True,'palette_audio_timing_exact':True,'support4_original_used_tiles_exact':True,'producer_packer_or_generation_called':False,'runtime_verified':False,'actual_viewed_packed_sheets':[],'limitations':['部分 VRAM bank1 42..49는 원시와 조립 보존만 확인했다.','머리 전체 재작화가 아니라 해당 각도의 기존 수용 머리를 보존하고 옷/부츠를 새 원화로 교체했다.','동적 화염과의 실제 연결·원래 MIPS/GPU 실행은 루트의 별도 검증이다.']}
sp=P/'static_effects.json'
if sp.exists():
    rec=json.loads(sp.read_text('utf8'));before=json.loads((ROOT/p['source_arc']).with_name('static_effects.json').read_text('utf8'));assert rec['parts_sha256']==sha(nc) and {k:v for k,v in rec.items()if k!='parts_sha256'}=={k:v for k,v in before.items()if k!='parts_sha256'};report['static_recipe_sha256']=sha(sp.read_bytes());report['static_recipe_only_parts_hash_rebound']=True
report['actual_viewed_packed_sheets']=[{'path':str((P/f'{mode}_readback_{i:02}.png').relative_to(ROOT)),'sha256':sha((P/f'{mode}_readback_{i:02}.png').read_bytes())}for mode in('normal','black')for i in range(4)]
report['visual_notes']=['일반/블랙 ARC 재독출 8장을 실제 열람했다. 머리 크기와 얼굴은 유지하고 상의·칼라·소매·부츠를 대기의 명암 밀도에 맞춰 세분화했다.','133..137의 망토 끝과 138..144의 손·망토 변화는 원래 순서이며 새로운 몸체 단절은 보이지 않는다.','146의 숙인 몸,156/158의 올린 손은 원래 방향을 유지하며 손잡이/목/허리 연결이 살아 있다. 화염과의 동적 접합은 정적 그림만으로 완료 처리하지 않는다.']
report['support_tile_layout_note']='원시 SPU가 아닌 그래픽 VRAM 행 단위 4bpp 배열이므로 indexed_atlas의 실제 16x16 창으로 비교했다. 지원4의19파트는 숨은 영역까지 동일하다.'
report['frozen']=True
O=H/'riko_rising_independent';O.mkdir(exist_ok=True);(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'counts':counts,'report':str(O/'verification.json')}))
