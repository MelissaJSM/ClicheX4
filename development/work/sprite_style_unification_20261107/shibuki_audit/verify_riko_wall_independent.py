"""리코 벽7의 원화와 머리/공유망토를 제작함수 없이 독립 재구성한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
H=Path(__file__).resolve().parent;W=H.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
sha=lambda b:hashlib.sha256(b).hexdigest()
P=W/'riko/prepared_wall_clothes_v1';p=json.loads((P/'proposal.json').read_text('utf8'))
old=(ROOT/p['source_arc']).read_bytes();new=(ROOT/p['resource']).read_bytes()
assert sha(old)==p['source_arc_sha256']=='aedbb93bf5072fbb5ba98ddd4c149b745849ac87173e965a1a2a8d7717ef1512'
assert sha(new)==p['after_sha256']=='8f81bd702370d9ae4d47a50cd6c628a9513067caeacf8de5ccff809097f06c48'
D=W/'riko/wall_clothes10';targets={};sources=[];masks={}
colors=np.array([[(v>>s&31)*255//31 for s in (0,5,10)]for v in struct.unpack_from('<16H',entry(old,9))],np.int32)
rects={37:(152,133,176,153),38:(142,128,167,148),**{n:(145,131,170,152)for n in range(39,44)}}
for folder in (D,D/'page2'):
    info=json.loads((folder/'inputs.json').read_text('utf8'));rd=folder/'registered01';reg=json.loads((rd/'registration.json').read_text('utf8'))
    assert info['sha256']==reg['source_sha256']==sha(old)
    im=Image.open(folder/'generated.png').convert('RGBA');assert sha((folder/'generated.png').read_bytes())==reg['generated_sha256']
    gx,gy=info['grid'];width=gx*96;scale=im.width/width;nh=round(im.height/scale)
    assert list(im.size)==reg['generated_dimensions'] and [width,nh]==reg['native_canvas'] and scale==reg['uniform_source_scale']
    pixels=np.array(im.resize((width,nh),Image.Resampling.NEAREST))
    idx=(1+((pixels[:,:,:3,None].transpose(0,1,3,2).astype(np.int32)-colors[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);idx[pixels[:,:,3]<128]=0
    for r in reg['frames']:
        n=r['ref'];spec=next(q for q in info['frames']if q['ref']==n);i=spec['cell']
        previous=render(old,0,0,n)[0];source=np.zeros_like(previous);cell=idx[i//gx*96:(i//gx+1)*96,i%gx*96:(i%gx+1)*96];source[112:112+cell.shape[0],112:208]=cell
        x0,y0,x1,y1=rects[n];head=previous[y0:y1,x0:x1];green=np.isin(head,[4,8,14]);options=[]
        for dy in range(-10,11):
            for dx in range(-8,9):
                q=source[y0-dy:y1-dy,x0-dx:x1-dx]
                error=int(np.count_nonzero(q[green]!=head[green])+np.count_nonzero(np.isin(q,[4,8,14])&~green))
                options.append((error,abs(dx)+abs(dy),dx,dy))
        _,_,dx,dy=min(options);assert [dx,dy]==r['generated_translation']
        authored=np.zeros_like(source);yy,xx=np.nonzero(source);authored[yy+dy,xx+dx]=source[yy,xx]
        assert np.array_equal(authored,np.array(Image.open(rd/f'b0_{n:03}_authored.png')))
        headmask=np.zeros_like(source,bool)
        for y,row in enumerate(head):
            xs=np.flatnonzero(row)
            if len(xs):headmask[y0+y,x0+xs.min():x0+xs.max()+1]=True
        window=np.zeros_like(headmask);window[y0-2:y1+2,x0-2:x1+2]=True
        extra=window&np.isin(authored,[4,8,14])&~headmask
        expected=authored.copy();expected[extra]=0;expected[headmask]=previous[headmask]
        assert list(rects[n])==r['head_rect'] and int(headmask.sum())==r['head_mask_pixels']
        assert np.array_equal(headmask,np.array(Image.open(rd/f'b0_{n:03}_head_mask.png'))>0)
        target=ROOT/r['target'];assert sha(target.read_bytes())==r['target_sha256'];assert np.array_equal(expected,np.array(Image.open(target)))
        assert r['hand_contact_exact'] is None
        targets[n]=expected;masks[n]=headmask
        sources.append({'ref':n,'source':str((folder/'generated.png').relative_to(ROOT)),'source_sha256':reg['generated_sha256'],'translation':[dx,dy],'head_pixels':int(headmask.sum()),'new_source_extra_green_cleared':int(extra.sum()),'source_registration_exact':True,'hands_not_pixel_guarded':True})
assert set(targets)==set(range(37,44))
oldframes={n:render(old,0,0,n)[0]for n in (41,42,43)}
variation=(oldframes[41]!=oldframes[42])|(oldframes[41]!=oldframes[43])
region=binary_dilation(variation,iterations=1);region[171:]=False
assert np.array_equal(region,np.array(Image.open(D/'targets01/cape_region.png'))>0)
loop=[]
for n in (42,43):
    assert np.array_equal(oldframes[n][~region],oldframes[41][~region])
    newpose=targets[41].copy();newpose[region]=targets[n][region];targets[n]=newpose
    loop.append({'ref':n,'master':41,'original_variable_pixels':int(variation.sum()),'one_pixel_extended_region':int(region.sum()),'common_new_body_outside_region_exact':True})
for r in p['registration']['frames']:
    n=r['ref'];path=ROOT/r['target'];assert sha(path.read_bytes())==r['target_sha256'];assert np.array_equal(targets[n],np.array(Image.open(path)))
assert set(p['target_references'])=={f'b0_{n:03}'for n in targets}

assert len(old)==len(new)
assert [(e['type'],e['offset'],e['size'])for e in psx_arc(old)]==[(e['type'],e['offset'],e['size'])for e in psx_arc(new)]
others=0
for e in psx_arc(old):
    if int(e['type'],16)not in(2,3):assert old[e['offset']:e['offset']+e['size']]==new[e['offset']:e['offset']+e['size']];others+=1
g,ng,c,nc=entry(old,2),entry(new,2),entry(old,3),entry(new,3)
assert bank_offsets(g)==bank_offsets(ng) and bank_offsets(c)==bank_offsets(nc)
assert g[bank_offsets(g)[1]:]==ng[bank_offsets(ng)[1]:]
semantic=lambda cp:[(v['flags'],v['tile'],v['x'],v['y'])for v in cp['parts']]
counts={'raw':0,'non_target_raw':0,'display':0,'non_target_display':0,'target_display':0,'other_parts':0,'known_partial_raw_parts_only':0,'gpu_parts':0,'existing_boundary_alpha':0,'new_boundary_alpha':0}
changes=[]
for b in (0,1):
    bb,nb=graphics_bank(g,b),graphics_bank(ng,b);assert len(bb['frames'])==len(nb['frames'])
    for f,z in zip(bb['frames'],nb['frames']):
        n=f['index'];counts['raw']+=1;assert f['tile_count']==z['tile_count']<=32
        raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        nr=decode_stream(ng,z['offset'],z['limit'],z['tile_count']*128).data
        target=b==0 and n in targets
        if not target:assert raw==nr;counts['non_target_raw']+=1
        cp,np_=composition_frame(c,b*5,n),composition_frame(nc,b*5,n)
        if not target:assert semantic(cp)==semantic(np_);counts['other_parts']+=1
        if b==1 and n in range(42,50):counts['known_partial_raw_parts_only']+=1;continue
        pix=render(new,b,b*5,n)[0];was=render(old,b,b*5,n)[0]
        assert np.array_equal(pix,targets[n]if target else was),(b,n,'display')
        counts['display']+=1
        if target:
            counts['target_display']+=1
            assert np.array_equal(pix[masks[n]],was[masks[n]])
            ta=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256)
            tb=np.frombuffer(indexed_atlas(nr,z['tile_count'])[0],np.uint8).reshape(-1,256)
            for q in np_['parts']:
                t=q['tile'];ox=t%16*16;oy=t//16*16
                if t%16==0:
                    counts['existing_boundary_alpha']+=int(np.count_nonzero(tb[oy:oy+16,ox]))
                    delta=(ta[oy:oy+16,ox]==0)&(tb[oy:oy+16,ox]>0);assert not delta.any();counts['new_boundary_alpha']+=int(delta.sum())
                if q['flip_y'] and t//16%16==0:assert not np.any((ta[oy,ox:ox+16]==0)&(tb[oy,ox:ox+16]>0))
                counts['gpu_parts']+=1
            changes.append({'ref':n,'changed_pixels':int(np.count_nonzero(pix!=was))})
        else:counts['non_target_display']+=1
assert counts['raw']==444 and counts['non_target_raw']==437 and counts['display']==436 and counts['non_target_display']==429
all_parts=0
for b in range(len(bank_offsets(c))):
    for n in range(composition_frame(c,b,0)['bank_frame_count']):
        cp,np_=composition_frame(c,b,n),composition_frame(nc,b,n)
        if b==0 and n==37:
            assert len(cp['parts'])==len(np_['parts'])
            for i,(q,r)in enumerate(zip(cp['parts'],np_['parts'])):
                assert (q['flags'],q['tile'],q['y'])==(r['flags'],r['tile'],r['y'])
                assert r['x']==q['x']-(1 if i in (0,1)else 0)
        else:assert semantic(cp)==semantic(np_);all_parts+=1
recipe=json.loads((P/'static_effects.json').read_text('utf8'));parent_recipe=json.loads((ROOT/p['source_arc']).with_name('static_effects.json').read_text('utf8'))
assert recipe['parts_sha256']==sha(nc)
assert sha((P/'static_effects.json').read_bytes())=='8c4b6ef5def82534ce929427a0aa311fef9e68b1ae9944b956cc93f0292192de'
assert {k:v for k,v in recipe.items()if k!='parts_sha256'}=={k:v for k,v in parent_recipe.items()if k!='parts_sha256'}
views=[str((P/f'{mode}_readback_{i:02}.png').relative_to(ROOT))for mode in ('normal','black')for i in range(2)]
report={'passed':True,'parent_sha256':sha(old),'candidate_sha256':sha(new),'proposal_sha256':sha((P/'proposal.json').read_bytes()),'source_reconstruction':sources,'cape_loop_reconstruction':loop,'counts':counts,'changes':changes,'all_other_composition_refs_exact':all_parts,'composition37_only_changes':'첫 두 파츠의 x만 -1. 새 그림을 원창에 넣으면서 실제 머리 좌표/색/알파는 보존.','bank1_graphics_bytes_exact':True,'non_graphics_entries_exact':others,'palette_audio_timing_exact':True,'static_recipe_sha256':sha((P/'static_effects.json').read_bytes()),'static_recipe_only_partshash_rebound':True,'producer_or_packer_called':False,'actual_view_image_files':views,'visual_notes':['일반·블랙7참조 모두 대기 옆에서 직접 열람했다. 칼라·소매·허리·부츠 명암이 분리되며 머리/몸 비율이 유지된다.','41~43은 같은 몸을 유지하고 망토의 실제 변화 구간만 달라져 호흡 몸통이 흔들리지 않는다.','몸을 굽힌 벽 자세의 다리 높이 차이는 정상 자세로 구분했다. 벽면과 손의 실제 게임 접촉은 이 미리보기로 검증하지 않는다.'],'limitations':['손 픽셀을 원본과 고정하는 마스크는 없으며 hand_contact_exact=None이다.','bank1 체이서42~49는 부분 업로드여서 원시/조립 보존만 검증했다. 이번 bank0 벽42/43과 다른 자원이다.','실제 MIPS/GPU 및 게임플레이는 루트 별도 검사다.'],'runtime_verified':False}
O=H/'riko_wall_independent';O.mkdir(exist_ok=True);(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'counts':counts,'other_parts':all_parts,'report':str(O/'verification.json')}))
