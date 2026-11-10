"""원화와 실제 ARC를 독립 대조한다. 등록기/패커 호출 및 원본 쓰기는 없다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent; W=H.parent; ROOT=W.parents[1]
sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets
sha=lambda b:hashlib.sha256(b).hexdigest()
P=W/'riko/prepared_jump_clothes_v1';p=json.loads((P/'proposal.json').read_text('utf8'))
old=(ROOT/p['source_arc']).read_bytes();new=(ROOT/p['resource']).read_bytes()
assert sha(old)==p['source_arc_sha256']=='7b79453e89d3a9600ee117630a510844a5738c31bf3e3e3d5b6ebac35b739328'
assert sha(new)==p['after_sha256']=='95867666de2ab6a0a3712de5b047a0c6f44fb827d74cc6b2d873f854739b84e9'
head=np.array(Image.open(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png'))[:19,12:35]
inside=np.zeros(head.shape,bool)
for y,row in enumerate(head):
    xs=np.flatnonzero(row)
    if len(xs):inside[y,xs[0]:xs[-1]+1]=True
assert inside.sum()==316
green=np.isin(head,[4,8,14]);targets={};source_checks=[]
def anchor(q,lo,hi):
    rows=[]
    for y in range(lo,hi):
        for x in range(125,170):
            crop=q[y:y+19,x:x+23]
            score=np.count_nonzero(crop[green]!=head[green])+np.count_nonzero(np.isin(crop,[4,8,14])&~green)
            rows.append((int(score),x,y))
    return min(rows)
for number in (1,2,3):
    d=W/f'riko/jump_clothes08/page{number}';rd=d/'registered02'
    reg=json.loads((rd/'registration.json').read_text('utf8'));info=json.loads((d/'inputs.json').read_text('utf8'))
    source=(ROOT/reg['source_arc']).read_bytes();assert source==old
    generated=(d/'generated.png').read_bytes();assert sha(generated)==reg['generated_sha256']
    im=Image.open(d/'generated.png').convert('RGBA');assert list(im.size)==reg['generated_dimensions']
    width=96*len(info['frames']);nh=round(im.height/(im.width/width));assert [width,nh]==reg['native_canvas']
    sample=np.array(im.resize((width,nh),Image.Resampling.NEAREST))
    words=struct.unpack_from('<16H',entry(source,9));rgb=np.array([[(v>>s&31)*255//31 for s in (0,5,10)]for v in words],np.int32)
    distance=((sample[:,:,:3].astype(np.int32)[:,:,None,:]-rgb[None,None,1:,:])**2).sum(3)
    index=(distance.argmin(2)+1).astype(np.uint8);index[sample[:,:,3]<128]=0
    for r in reg['frames']:
        b,n=r['bank'],r['ref'];spec=next(x for x in info['frames']if x['bank']==b and x['ref']==n)
        previous=render(old,b,b*5,n)[0];score,hx,hy=anchor(previous,115,155);assert score==0
        assert [hx-160,hy-160]==r['source_head_anchor']
        raw=np.zeros((384,384),np.uint8);raw[112:112+nh,112:208]=index[:,96*spec['cell']:96*(spec['cell']+1)]
        _,gx,gy=anchor(raw,115,170);expected_translation=[hx-gx,hy-gy]
        if n==24:expected_translation[0]=0
        assert expected_translation==r['generated_translation']
        dx,dy=expected_translation;yy,xx=np.nonzero(raw);expected=np.zeros_like(raw);expected[yy+dy,xx+dx]=raw[yy,xx]
        assert np.array_equal(expected,np.array(Image.open(rd/f'b{b}_{n:03}_authored.png')))
        mask=np.zeros_like(raw,bool);mask[hy:hy+19,hx:hx+23]=inside;expected[mask]=previous[mask]
        assert r['contact_rects']==[] and r['hand_contact_exact'] is None and r['registration_parts']==[]
        target=ROOT/r['target'];assert sha(target.read_bytes())==r['target_sha256']
        assert np.array_equal(expected,np.array(Image.open(target))),(b,n,'source reconstruction')
        assert np.array_equal(mask,np.array(Image.open(rd/f'b{b}_{n:03}_head_mask.png'))>0)
        targets[b,n]=expected
        source_checks.append(dict(bank=b,ref=n,source_generated_sha256=sha(generated),target_sha256=sha(target.read_bytes()),head_pixels=316,translation=expected_translation,body_x_exception=n==24,hand_contact_exact=None,exact=True))
assert len(targets)==8
aliases={23:22,26:25,28:27,29:27,30:27,31:27,32:27}
for n,master in aliases.items():
    assert np.array_equal(render(old,0,0,n)[0],render(old,0,0,master)[0])
    targets[0,n]=targets[0,master].copy()
assert {f'b{b}_{n:03}'for b,n in targets}==set(p['target_references'])
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
assert counts['target_exact']==15 and counts['unaffected_raw']==429 and counts['other_display']==421
assert entry(old,0x10206)==entry(new,0x10206)
recipe=json.loads((P/'static_effects.json').read_text('utf8'));assert recipe['parts_sha256']==sha(nc)
assert sha((P/'static_effects.json').read_bytes())=='51240f2d169a254d3dc4a7bf649a35240f56faccdbef6315dae8e40d3dc03432'
report=dict(passed=True,source_sha256=sha(old),candidate_sha256=sha(new),proposal_sha256=sha((P/'proposal.json').read_bytes()),source_reconstruction=source_checks,aliases=aliases,counts=counts,changes=changes,non_graphic_entries_exact=other_entries,palette_audio_timing_exact=True,static_texture_exact=True,static_recipe_rebound_to_composition=True,producer_or_packer_called=False,visual_review=[],runtime_verified=False,limitations=['손 접점은 원본 정확 보존 대상으로 지정되지 않았다. 새 손 모양은 미술 검토이며 판정 변경이 아니다.','24의 몸체 x0 등록 예외를 원화와 직접 대조했다. 머리316 픽셀은 원래 위치를 보존했다.','부분 VRAM 업로드 42..49는 원시 데이터와 조립만 보존 검사했다.','에뮬레이터 실기 및 모든 동작의 미술 완료는 별도다.'])
dest=H/'riko_jump_independent';dest.mkdir(exist_ok=True)
report['visual_review']=[str((P/f'{mode}_readback_{i:02}.png').relative_to(ROOT))for mode in('normal','black')for i in range(4)]
report['visual_notes']=['일반/블랙 각각4장 전체15참조를 실제 열람했다. 대기 머리의 크기·명암은 보존되며 소매·칼라·허리·부츠와 망토의 면 분할이 개선됐다.','21/22/24의 굽힌 무릎,27 및 별칭의 세워진 망토,33의 착지,35/36의 양팔 자세는 서로 다른 정상 자세로 구분했다.','손 좌표 정확 보존은 미보장이며 실제 플레이의 판정·이펙트 연결 검증을 대신하지 않는다. 새 그림에서 명백한 손목 분리나 머리 크기 변화는 보이지 않았다.']
(dest/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(dict(passed=True,counts=counts,report=str(dest/'verification.json'))))
