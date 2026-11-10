"""체이서26: 원화 등록과 원래 망토를 별도로 복원하여 준비 ARC를 독립 검사."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;W=H.parent;ROOT=W.parents[1]
sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices,bank_offsets
sha=lambda b:hashlib.sha256(b).hexdigest()
P=W/'riko/prepared_vehicle_clothes_v2';p=json.loads((P/'proposal.json').read_text('utf8'))
old=(ROOT/p['source_arc']).read_bytes();new=(ROOT/p['resource']).read_bytes()
assert sha(old)==p['source_arc_sha256']=='95867666de2ab6a0a3712de5b047a0c6f44fb827d74cc6b2d873f854739b84e9'
assert sha(new)==p['after_sha256']=='aedbb93bf5072fbb5ba98ddd4c149b745849ac87173e965a1a2a8d7717ef1512'
ancestor=(W/'riko/prepared_head_spaces_v1/PL01_U.ARC').read_bytes()
assert sha(ancestor)=='488b679ed027fd8916e0f48716c9e3fa65d03ff42d4ac21d38dffb6ed0a7edaf'
D=W/'riko/vehicle_clothes09';rd=D/'registered01'
reg=json.loads((rd/'registration.json').read_text('utf8'));info=json.loads((D/'inputs.json').read_text('utf8'))
assert reg['source_sha256']==sha(old) and (ROOT/reg['source_arc']).read_bytes()==old
im=Image.open(D/'generated.png').convert('RGBA');assert sha((D/'generated.png').read_bytes())==reg['generated_sha256']
assert list(im.size)==reg['generated_dimensions'];nh=round(im.height/(im.width/288));assert [288,nh]==reg['native_canvas']
sample=np.array(im.resize((288,nh),Image.Resampling.NEAREST))
colors=np.array([[(v>>s&31)*255//31 for s in(0,5,10)]for v in struct.unpack_from('<16H',entry(old,9))],np.int32)
idx=(1+((sample[:,:,:3,None].transpose(0,1,3,2).astype(np.int32)-colors[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8)
idx[sample[:,:,3]<128]=0
heads={25:(140,142,171,160),33:(142,136,173,153),41:(148,134,178,154)}
hands={25:(140,160,150,167),33:(141,153,151,160),41:(144,152,154,159)}
masters={17:render(old,1,5,17)[0]};source_checks=[]
for r in reg['frames']:
 n=r['ref'];assert n in heads
 spec=next(v for v in info['frames']if v['ref']==n)
 previous=render(old,1,5,n)[0];raw=np.zeros((384,384),np.uint8);raw[112:112+nh,112:208]=idx[:,96*spec['cell']:96*(spec['cell']+1)]
 x0,y0,x1,y1=heads[n];head=previous[y0:y1,x0:x1];green=np.isin(head,[4,8,14]);candidates=[]
 for dy in range(-16,17):
  for dx in range(-5,6):
   q=raw[y0-dy:y1-dy,x0-dx:x1-dx]
   error=np.count_nonzero(q[green]!=head[green])+np.count_nonzero(np.isin(q,[4,8,14])&~green)
   candidates.append((int(error),abs(dx)+abs(dy),dx,dy))
 _,_,dx,dy=min(candidates);assert [dx,dy]==r['generated_translation']
 yy,xx=np.nonzero(raw);authored=np.zeros_like(raw);authored[yy+dy,xx+dx]=raw[yy,xx]
 assert np.array_equal(authored,np.array(Image.open(rd/f'b1_{n:03}_authored.png')))
 mask=np.zeros_like(raw,bool)
 for j,row in enumerate(head):
  xs=np.flatnonzero(row)
  if len(xs):mask[y0+j,x0+xs[0]:x0+xs[-1]+1]=True
 window=np.zeros_like(mask);window[y0-2:y1+2,x0-2:x1+2]=True
 extra=window&np.isin(authored,[4,8,14])&~mask
 expected=authored.copy();expected[extra]=0;expected[mask]=previous[mask]
 hx0,hy0,hx1,hy1=hands[n];hm=np.zeros_like(mask);hm[hy0:hy1,hx0:hx1]=True;expected[hm]=previous[hm]
 assert list(heads[n])==r['head_rect'] and list(hands[n])==r['hand_rect'] and int(mask.sum())==r['head_mask_pixels']
 assert int(extra.sum())==r['cleared_generated_extra_green']
 target=ROOT/r['target'];assert sha(target.read_bytes())==r['target_sha256'];assert np.array_equal(expected,np.array(Image.open(target)))
 assert np.array_equal(mask,np.array(Image.open(rd/f'b1_{n:03}_head_mask.png'))>0)
 assert np.array_equal(hm,np.array(Image.open(rd/f'b1_{n:03}_hand_mask.png'))>0)
 masters[n]=expected;source_checks.append(dict(ref=n,translation=[dx,dy],head_pixels=int(mask.sum()),hand_rect=hands[n],exact=True))
BODY={12,13,14,15,28,29,30,31}
def selected(data,n,body):
 g,c=entry(data,2),entry(data,3);f=graphics_bank(g,1)['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;cp=composition_frame(c,5,n)
 cp['parts']=[q for q in cp['parts']if(q['tile']in BODY)==body]
 pix,size,bb,_=compose_indices(raw,f['tile_count'],cp);small=np.frombuffer(pix,np.uint8).reshape(size[1],size[0]);out=np.zeros((384,384),np.uint8)
 yy,xx=np.nonzero(small);out[yy+160+bb[1],xx+160+bb[0]]=small[yy,xx];return out
def shift(q,dy):
 out=np.zeros_like(q);yy,xx=np.nonzero(q);out[yy+dy,xx]=q[yy,xx];return out
targets={};variant_checks=[];vr=json.loads((D/'variants02/registration.json').read_text('utf8'))
for k,start,end in[(17,14,22),(25,22,30),(33,30,38),(41,38,42)]:
 source=ancestor if k==17 else old;body=selected(source,k,True)
 cape_union=np.logical_or.reduce([selected(source,n,False)>0 for n in range(start,start+4)])
 yy,xx=np.nonzero(cape_union);region=np.zeros_like(body,bool);region[yy.min()-2:yy.max()+3,xx.min()-2:xx.max()+3]=True
 key=masters[k].copy();key[region&(body==0)]=0
 for n in range(start,end):
  if n in(17,20):continue
  dy={4:1,5:2,6:1,7:-1}.get(n-start,0);r=next(v for v in vr['frames']if v['ref']==n)
  assert r['translation']==[0,dy] and r['master']==k
  assert np.array_equal(selected(source,n,True),shift(body,dy))
  authored=shift(key,dy);cape=selected(source,n,False);expected=cape.copy();expected[authored>0]=authored[authored>0]
  target=ROOT/r['target'];assert sha(target.read_bytes())==r['target_sha256'];assert np.array_equal(expected,np.array(Image.open(target)))
  targets[1,n]=expected;variant_checks.append(dict(ref=n,master=k,translation=[0,dy],original_cape_visible_pixels=int(((cape>0)&(authored==0)).sum()),new_body_pixels=int((authored>0).sum()),exact=True))
assert len(targets)==26 and {f'b{b}_{n:03}'for b,n in targets}==set(p['target_references'])

assert len(old)==len(new)
assert [(e['type'],e['offset'],e['size'])for e in psx_arc(old)]==[(e['type'],e['offset'],e['size'])for e in psx_arc(new)]
other_entries=0
for e in psx_arc(old):
    if int(e['type'],16)not in(2,3):
        start=e['offset'];end=start+e['size'];assert old[start:end]==new[start:end];other_entries+=1
g,ng,c,nc=entry(old,2),entry(new,2),entry(old,3),entry(new,3)
assert bank_offsets(g)==bank_offsets(ng);assert bank_offsets(c)==bank_offsets(nc)
sem=lambda cp:[(v['flags'],v['tile'],v['x'],v['y'])for v in cp['parts']]
def tiles(data,count):
    u=np.frombuffer(data,np.uint8);pix=np.empty(len(data)*2,np.uint8);pix[::2]=u&15;pix[1::2]=u>>4
    result=[];cursor=0
    for start in range(0,count,16):
        length=min(16,count-start);block=pix[cursor:cursor+length*256].reshape(16,length*16)
        result.extend(block[:,i*16:(i+1)*16]for i in range(length));cursor+=length*256
    return np.array(result)
counts=dict(raw=0,unaffected_raw=0,display=0,target_exact=0,other_display=0,other_parts=0,gpu_parts=0,existing_boundary_alpha=0,new_boundary_alpha=0,known_partial_not_reconstructed=0)
changes=[]
for b in(0,1):
    before=graphics_bank(g,b);after=graphics_bank(ng,b)
    selected_offsets={before['frames'][n]['offset']for bb,n in targets if bb==b}
    assert len(before['frames'])==len(after['frames'])
    for a,z in zip(before['frames'],after['frames']):
        n=a['index'];counts['raw']+=1;assert a['tile_count']==z['tile_count']<=32
        raw=decode_stream(g,a['offset'],a['limit'],a['tile_count']*128).data
        nraw=decode_stream(ng,z['offset'],z['limit'],z['tile_count']*128).data
        if a['offset']not in selected_offsets:assert raw==nraw;counts['unaffected_raw']+=1
        cp=composition_frame(c,b*5,n);ncp=composition_frame(nc,b*5,n)
        if(b,n)not in targets:assert sem(cp)==sem(ncp);counts['other_parts']+=1
        if b==1 and 42<=n<=49:counts['known_partial_not_reconstructed']+=1;continue
        op=render(old,b,b*5,n)[0];npix=render(new,b,b*5,n)[0]
        assert np.array_equal(npix,targets.get((b,n),op)),(b,n,'readback');counts['display']+=1
        if(b,n)in targets:
            counts['target_exact']+=1;changes.append(dict(bank=b,ref=n,pixels=int(np.count_nonzero(op!=npix))))
            oldtiles,newtiles=tiles(raw,a['tile_count']),tiles(nraw,z['tile_count'])
            for part in ncp['parts']:
                t=part['tile'];assert t<len(newtiles)
                if t%16==0:
                    counts['existing_boundary_alpha']+=int(np.count_nonzero(newtiles[t,:,0]))
                    added=np.count_nonzero((oldtiles[t,:,0]==0)&(newtiles[t,:,0]>0));assert not added
                    counts['new_boundary_alpha']+=int(added)
                if part['flags']&128 and t//16%16==0:assert not np.any((oldtiles[t,0,:]==0)&(newtiles[t,0,:]>0))
                counts['gpu_parts']+=1
        else:counts['other_display']+=1
assert counts['target_exact']==26 and counts['unaffected_raw']==418 and counts['other_display']==410
assert entry(old,0x10206)==entry(new,0x10206)
recipe=json.loads((P/'static_effects.json').read_text('utf8'));assert recipe['parts_sha256']==sha(nc)
assert sha((P/'static_effects.json').read_bytes())=='6b425cb23925734bede2304d9bf16fdb5ea14273d1c608868e7b3cdbc72b28d0'
cape_records=0;cape_tile_checks=0
for b,n in targets:
 cp=composition_frame(c,5,n);ncp=composition_frame(nc,5,n)
 oldcape=[c[q['record_offset']:q['record_offset']+4]for q in cp['parts']if q['tile']not in BODY]
 newcape=[nc[q['record_offset']:q['record_offset']+4]for q in ncp['parts']if q['tile']not in BODY]
 assert oldcape==newcape,(n,'original cape records');cape_records+=len(oldcape)
 a=graphics_bank(g,1)['frames'][n];z=graphics_bank(ng,1)['frames'][n]
 raw=tiles(decode_stream(g,a['offset'],a['limit'],a['tile_count']*128).data,a['tile_count'])
 nr=tiles(decode_stream(ng,z['offset'],z['limit'],z['tile_count']*128).data,z['tile_count'])
 for t in range(32):
  if t not in BODY:assert np.array_equal(raw[t],nr[t]);cape_tile_checks+=1
 assert np.array_equal(selected(old,n,False),selected(new,n,False))
for n in(17,20):
 assert np.array_equal(render(old,1,5,n)[0],render(new,1,5,n)[0])
 assert sem(composition_frame(c,5,n))==sem(composition_frame(nc,5,n))
views=[str((P/f'{mode}_readback_{i:02}.png').relative_to(ROOT))for mode in('normal','black')for i in range(7)]
for mode in('normal','black'):
 for i in range(7):
  v2=P/f'{mode}_readback_{i:02}.png';v1=W/'riko/prepared_vehicle_clothes_v1'/v2.name
  assert np.array_equal(np.array(Image.open(v2)),np.array(Image.open(v1))),'V2 readback differs from actually viewed v1'
report=dict(passed=True,parent_sha256=sha(old),candidate_sha256=sha(new),proposal_sha256=sha((P/'proposal.json').read_bytes()),
 source_reconstruction=source_checks,variant_reconstruction=variant_checks,counts=counts,changes=changes,
 original_cape_records_exact=cape_records,non_body_tiles_exact=cape_tile_checks,original_17_20_exact=True,
 original_partial_42_49_raw_parts_preserved=True,non_graphic_entries_exact=other_entries,
 palette_audio_timing_exact=True,static_texture_exact=True,static_recipe_sha256=sha((P/'static_effects.json').read_bytes()),
 producer_or_packer_called=False,visual_review=views,visual_basis='v1 일반/블랙14장을 실제 열람했고 v2의14PNG가 전픽셀 동일함을 별도로 확인했다.',
 visual_notes=['일반/블랙 각7장 전26참조를 실제 열람했다. 같은 원점에서 얼굴·머리크기와 조종손을 보존하고 가슴 여밈·소매·부츠/옷단 구분이 늘었다.',
 '기존망토 네 단계의 외곽·청록 안쪽이 새 몸 뒤로 연속된다. 기울어진 자세나 앉은 짧은 높이는 정상으로 구분하며 몸 전체를 키우지 않았다.',
 '순색/무채색에서 새 소매가 분리되거나 목이 끊어진 흔적은 보이지 않았다. 실제 차량 핸들·좌석과의 게임 합성은 이 시트로 증명하지 않는다.'],
 runtime_verified=False,limitations=['부분 업로드42..49는 독립 완성그림을 만들지 않고 원시/조립 보존만 확인했다.','에뮬레이터 차량 실기와 모든 동작의 미술 완료는 별도다.'])
dest=H/'riko_vehicle_independent';dest.mkdir(exist_ok=True)
(dest/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(dict(passed=True,counts=counts,cape_records=cape_records,non_body_tiles=cape_tile_checks,report=str(dest/'verification.json'))))
