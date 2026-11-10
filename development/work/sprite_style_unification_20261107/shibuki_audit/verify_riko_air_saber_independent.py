"""등록기/패커를 실행하지 않고 원화 픽셀부터 리코 공중13참조를 재구성한다."""
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
sha=lambda x:hashlib.sha256(x).hexdigest()
P=W/'riko/prepared_air_saber_v1'; p=json.loads((P/'proposal.json').read_text('utf8'))
old=(ROOT/p['source_arc']).read_bytes();new=(ROOT/p['resource']).read_bytes()
assert sha(old)==p['source_arc_sha256']=='105a7ba315a8dc0ef09d229770c4238fd8364adba43b483a5364c83f0ba79141'
assert sha(new)==p['after_sha256']=='7b79453e89d3a9600ee117630a510844a5738c31bf3e3e3d5b6ebac35b739328'
head=np.array(Image.open(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png'))[:19,12:35]
inside=np.zeros(head.shape,bool)
for y,row in enumerate(head):
    xx=np.flatnonzero(row)
    if len(xx):inside[y,xx[0]:xx[-1]+1]=True
assert inside.sum()==316
green=np.isin(head,[4,8,14]);targets={};source_checks=[]
folders=['followup_cloth05/registered03']+[f'air_saber_followup07/page{i}/registered02' for i in (1,2,3)]
for folder in folders:
    regdir=W/'riko'/folder;reg=json.loads((regdir/'registration.json').read_text('utf8'));d=regdir.parent
    source=(ROOT/reg['source_arc']).read_bytes();assert sha(source)==reg['source_sha256']
    generated=(d/'generated.png').read_bytes();assert sha(generated)==reg['generated_sha256']
    info=json.loads((d/'inputs.json').read_text('utf8'))
    im=Image.open(d/'generated.png').convert('RGBA'); assert list(im.size)==reg['generated_dimensions']
    width=96*len(info['frames']);nh=round(im.height/(im.width/width))
    assert [width,nh]==reg['native_canvas']
    sample=np.array(im.resize((width,nh),Image.Resampling.NEAREST))
    words=struct.unpack_from('<16H',entry(source,9));rgb=np.array([[(v>>s&31)*255//31 for s in (0,5,10)] for v in words],np.int32)
    squared=((sample[:,:,:3].astype(np.int32)[:,:,None,:]-rgb[None,None,1:,:])**2).sum(3)
    index=(squared.argmin(2)+1).astype(np.uint8);index[sample[:,:,3]<128]=0
    for r in reg['frames']:
        b,n=r['bank'],r['ref']
        if folder.startswith('followup') and n!=230:continue
        spec=next(x for x in info['frames'] if x['ref']==n and x['bank']==b)
        previous=render(source,b,b*5,n)[0]
        hx,hy=np.array(r['source_head_anchor'])+160
        assert np.array_equal(previous[hy:hy+19,hx:hx+23][head>0],head[head>0])
        dx,dy=r['generated_translation'];cell=index[:,96*spec['cell']:96*(spec['cell']+1)]
        expected=np.zeros((384,384),np.uint8)
        yy,xx=np.nonzero(cell);expected[yy+112+dy,xx+112+dx]=cell[yy,xx]
        mask=np.zeros_like(expected,bool);mask[hy:hy+19,hx:hx+23]=inside
        expected[mask]=previous[mask]
        rectangles=r.get('contact_rects',[[137,153,145,159]] if n==230 else [])
        contact=np.zeros_like(mask)
        for x0,y0,x1,y1 in rectangles:contact[y0:y1,x0:x1]=True
        expected[contact]=previous[contact]
        boot_pixels=0
        if n in (244,246):
            assert r['registration_parts'][0]['region']==[130,173,190,186]
            assert r['registration_parts'][0]['translation']==[0,-1]
            boot=np.zeros_like(mask);boot[173:186,130:190]=expected[173:186,130:190]>0
            yy,xx=np.nonzero(boot);values=expected[yy,xx].copy();expected[yy,xx]=0;expected[yy-1,xx]=values
            boot_pixels=len(xx);assert boot_pixels==r['registration_parts'][0]['pixels']
        target=ROOT/r['target'];assert sha(target.read_bytes())==r['target_sha256']
        assert np.array_equal(expected,np.array(Image.open(target))),(b,n,'source reconstruction')
        assert np.array_equal(expected[mask],previous[mask])
        assert np.array_equal(expected[contact],previous[contact])
        assert np.array_equal(render(old,b,b*5,n)[0],previous)
        targets[b,n]=expected
        source_checks.append(dict(bank=b,ref=n,generated_sha256=sha(generated),target_sha256=sha(target.read_bytes()),head_pixels=316,hand_pixels=int(contact.sum()),boot_translation_pixels=boot_pixels,exact=True))
for n in (133,134):
    assert np.array_equal(render(old,0,0,n)[0],render(old,0,0,246)[0]);targets[0,n]=targets[0,246].copy()
earlier_path=W/'riko/prepared_ceremony_v2/PL01_U.ARC';earlier=earlier_path.read_bytes()
assert sha(earlier)=='590ed75799910795db7f237688bbd10ef3a282a7d12910956d798f497e67f818'
old185=render(earlier,1,5,185)[0];master=render(old,1,5,185)[0]
cape=np.zeros_like(master,bool);cape[140:155,152:163]=True
for n in (186,187):
    before=render(old,1,5,n)[0]
    assert np.array_equal(before,render(earlier,1,5,n)[0]);assert np.array_equal(before[~cape],old185[~cape])
    expected=master.copy();expected[cape]=before[cape];targets[1,n]=expected
    assert np.array_equal(expected,np.array(Image.open(W/f'riko/burst_exit_registered01/b1_{n:03}_indices.png')))
assert len(targets)==13
assert {f'b{b}_{n:03}' for b,n in targets}==set(p['target_references'])
assert len(old)==len(new)
assert [(e['type'],e['offset'],e['size']) for e in psx_arc(old)]==[(e['type'],e['offset'],e['size']) for e in psx_arc(new)]
other_entries=0
for e in psx_arc(old):
    if int(e['type'],16) not in (2,3):
        start=e['offset'];end=start+e['size'];assert old[start:end]==new[start:end];other_entries+=1
g,ng,c,nc=entry(old,2),entry(new,2),entry(old,3),entry(new,3)
assert bank_offsets(g)==bank_offsets(ng);assert bank_offsets(c)==bank_offsets(nc)
sem=lambda cp:[(v['flags'],v['tile'],v['x'],v['y']) for v in cp['parts']]
counts=dict(raw=0,unaffected_raw=0,display=0,target_exact=0,other_display=0,other_parts=0,gpu_parts=0,existing_boundary_alpha=0,new_boundary_alpha=0,known_partial_not_reconstructed=0)
changed=[]
for b in (0,1):
    before=graphics_bank(g,b);after=graphics_bank(ng,b)
    selected_offsets={before['frames'][n]['offset'] for bb,n in targets if bb==b}
    for a,z in zip(before['frames'],after['frames']):
        n=a['index'];counts['raw']+=1;assert a['tile_count']==z['tile_count']<=32
        raw=decode_stream(g,a['offset'],a['limit'],a['tile_count']*128).data
        nraw=decode_stream(ng,z['offset'],z['limit'],z['tile_count']*128).data
        if a['offset'] not in selected_offsets:assert raw==nraw;counts['unaffected_raw']+=1
        cp=composition_frame(c,b*5,n);ncp=composition_frame(nc,b*5,n)
        if (b,n) not in targets:assert sem(cp)==sem(ncp);counts['other_parts']+=1
        if b==1 and 42<=n<=49:counts['known_partial_not_reconstructed']+=1;continue
        oldpixels=render(old,b,b*5,n)[0];pixels=render(new,b,b*5,n)[0]
        assert np.array_equal(pixels,targets.get((b,n),oldpixels)),(b,n,'readback')
        counts['display']+=1
        if (b,n)in targets:
            counts['target_exact']+=1;changed.append(dict(bank=b,ref=n,changed_pixels=int(np.count_nonzero(pixels!=oldpixels))))
        else:counts['other_display']+=1
        if (b,n)in targets:
            def tile_rows(data,count):
                u=np.frombuffer(data,np.uint8);pixels=np.empty(len(data)*2,np.uint8);pixels[::2]=u&15;pixels[1::2]=u>>4
                result=[];cursor=0
                for start in range(0,count,16):
                    length=min(16,count-start);block=pixels[cursor:cursor+length*256].reshape(16,length*16)
                    result.extend(block[:,i*16:(i+1)*16] for i in range(length));cursor+=length*256
                return np.array(result)
            tiles=tile_rows(nraw,z['tile_count']);previous_tiles=tile_rows(raw,a['tile_count'])
            for part in ncp['parts']:
                t=part['tile'];assert t<len(tiles)
                if t%16==0:
                    counts['existing_boundary_alpha']+=int(np.count_nonzero(tiles[t,:,0]))
                    added=np.count_nonzero((previous_tiles[t,:,0]==0)&(tiles[t,:,0]>0));assert not added
                    counts['new_boundary_alpha']+=int(added)
                if part['flags']&128 and t//16%16==0:
                    assert not np.any((previous_tiles[t,0,:]==0)&(tiles[t,0,:]>0))
                counts['gpu_parts']+=1
assert counts['target_exact']==13
assert entry(old,0x10206)==entry(new,0x10206),'Static texture must remain unchanged'
recipe=json.loads((P/'static_effects.json').read_text('utf8'));assert recipe['parts_sha256']==sha(nc)
report=dict(passed=True,source_sha256=sha(old),candidate_sha256=sha(new),proposal_sha256=sha((P/'proposal.json').read_bytes()),source_reconstruction=source_checks,
    counts=counts,changes=changed,non_graphic_entries_exact=other_entries,palette_audio_timing_exact=True,
    source_head_mask=316,aliases_133_134_equal_246=True,burst185_cape_variant_preserved=True,
    static_texture_exact=True,static_recipe_rebound_to_composition=True,producer_or_packer_called=False,
    visual_review=[str((P/f'{mode}_readback_{i:02}.png').relative_to(ROOT)) for mode in ('normal','black') for i in range(4)],
    visual_notes=['일반/블랙 각4장 실제 열람. 대기의 머리 밀도와 새 칼라·소매·치마 주름 연결을 확인했다.','244/246의 부츠 한 픽셀 상향은 머리·손을 이동하지 않았으며 133/134 복제와 동일하다.','186/187은 숙인 공격 자세를 유지하며 기존 망토 끝 두 변형을 새185 몸체에 연결한다.'],
    runtime_verified=False,limitations=['부분 VRAM 업로드 42..49는 원시 데이터/조립 보존만 검사; 가짜 완성 그림을 만들지 않음.','실제 게임 입력/실행 검증은 별도.'])
dest=H/'riko_air_saber_independent';dest.mkdir(exist_ok=True)
(dest/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(dict(passed=True,counts=counts,report=str(dest/'verification.json'))))
