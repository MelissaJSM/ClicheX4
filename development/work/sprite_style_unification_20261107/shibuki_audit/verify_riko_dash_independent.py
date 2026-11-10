"""리코 대시9의 원화 등록·공유 몸체·GPU 범위를 제작 함수 없이 재검증한다."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
H=Path(__file__).resolve().parent;W=H.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
sha=lambda b:hashlib.sha256(b).hexdigest()
P=W/'riko/prepared_dash_clothes_v1';p=json.loads((P/'proposal.json').read_text('utf8'))
old=(ROOT/p['source_arc']).read_bytes();new=(ROOT/p['resource']).read_bytes()
assert sha(old)==p['source_arc_sha256']=='8f81bd702370d9ae4d47a50cd6c628a9513067caeacf8de5ccff809097f06c48'
assert sha(new)==p['after_sha256']=='93844db97721cc95c89ece5a81eb48d9135f1e0f2c5aafb172d2890b11bff1b5'
D=W/'riko/dash_clothes11';colors=np.array([[(v>>s&31)*255//31 for s in(0,5,10)]for v in struct.unpack_from('<16H',entry(old,9))],np.int32)
head_path=ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png'
head=np.array(Image.open(head_path))[:19,12:35];green=np.isin(head,[4,8,14]);height,width=head.shape;inside=np.zeros_like(head,bool)
for y,row in enumerate(head):
    xs=np.flatnonzero(row)
    if len(xs):inside[y,xs.min():xs.max()+1]=True
assert int(inside.sum())==316
def anchor(a,lo,hi):
    best=[]
    for y in range(lo,hi):
        for x in range(125,170):
            q=a[y:y+height,x:x+width]
            error=np.count_nonzero(q[green]!=head[green])+np.count_nonzero(np.isin(q,[4,8,14])&~green)
            best.append((int(error),x,y))
    return min(best)
targets={};masks={};sources=[]
for page,folder in [(1,'registered02'),(2,'registered01'),(3,'registered01')]:
    d=D/f'page{page}';info=json.loads((d/'inputs.json').read_text('utf8'));reg=json.loads((d/folder/'registration.json').read_text('utf8'))
    assert info['sha256']==reg['source_sha256']==sha(old)
    im=Image.open(d/'generated.png').convert('RGBA');assert sha((d/'generated.png').read_bytes())==reg['generated_sha256']
    nw=len(info['frames'])*96;scale=im.width/nw;nh=round(im.height/scale)
    assert [nw,nh]==reg['native_canvas'] and list(im.size)==reg['generated_dimensions'] and scale==reg['uniform_source_scale']
    rgba=np.array(im.resize((nw,nh),Image.Resampling.NEAREST));rgb=rgba[:,:,:3].astype(np.int32)
    idx=(1+((rgb[:,:,None,:]-colors[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);idx[rgba[:,:,3]<128]=0
    for row in reg['frames']:
        n=row['ref'];spec=next(x for x in info['frames']if x['ref']==n);previous=render(old,0,0,n)[0]
        generated=np.zeros_like(previous);generated[112:112+nh,112:208]=idx[:,spec['cell']*96:(spec['cell']+1)*96]
        mismatch,hx,hy=anchor(previous,115,155);assert np.array_equal(previous[hy:hy+height,hx:hx+width][inside],head[inside])
        _,gx,gy=anchor(generated,115,170);dx,dy=hx-gx,hy-gy
        assert [hx-160,hy-160]==row['source_head_anchor'] and [dx,dy]==row['generated_translation']
        authored=np.zeros_like(previous);yy,xx=np.nonzero(generated);authored[yy+dy,xx+dx]=generated[yy,xx]
        assert np.array_equal(authored,np.array(Image.open(d/folder/f'b0_{n:03}_authored.png')))
        mask=np.zeros_like(previous,bool);mask[hy:hy+height,hx:hx+width]=inside
        assert np.array_equal(mask,np.array(Image.open(d/folder/f'b0_{n:03}_head_mask.png'))>0)
        result=authored.copy();result[mask]=previous[mask]
        target=ROOT/row['target'];assert sha(target.read_bytes())==row['target_sha256'];assert np.array_equal(result,np.array(Image.open(target)))
        assert row['contact_rects']==[] and row['hand_contact_exact']is None
        targets[n]=result;masks[n]=mask
        sources.append({'ref':n,'source':str((d/'generated.png').relative_to(ROOT)),'source_sha256':reg['generated_sha256'],'fixed_scale':scale,'translation':[dx,dy],'head_anchor_world':[hx-160,hy-160],'original_anchor_score':mismatch,'head_inside_pixels_exact':316,'source_reconstruction_exact':True,'hand_and_boot_pixels_not_guarded':True})
assert set(targets)==set(range(44,53))
oldframes={n:render(old,0,0,n)[0]for n in targets}
variation=(oldframes[46]!=oldframes[47])|(oldframes[48]!=oldframes[47]);region=binary_dilation(variation,iterations=1);region[171:]=False
assert np.array_equal(region,np.array(Image.open(D/'targets01/cape_region.png'))>0)
for n in(46,48):
    assert np.array_equal(oldframes[n][~region],oldframes[47][~region]);result=targets[47].copy();result[region]=targets[n][region];targets[n]=result
assert not oldframes[51][:,0].any() and np.array_equal(np.roll(oldframes[51],-1,axis=1),oldframes[52])
assert not targets[51][:,0].any();targets[52]=np.roll(targets[51],-1,axis=1)
for row in p['registration']['frames']:
    q=ROOT/row['target'];assert sha(q.read_bytes())==row['target_sha256'];assert np.array_equal(targets[row['ref']],np.array(Image.open(q)))
assert set(p['target_references'])=={f'b0_{n:03}'for n in targets}
assert len(old)==len(new) and [(e['type'],e['offset'],e['size'])for e in psx_arc(old)]==[(e['type'],e['offset'],e['size'])for e in psx_arc(new)]
other_entries=0
for e in psx_arc(old):
    if int(e['type'],16)not in(2,3):assert old[e['offset']:e['offset']+e['size']]==new[e['offset']:e['offset']+e['size']];other_entries+=1
g,ng,c,nc=entry(old,2),entry(new,2),entry(old,3),entry(new,3)
assert bank_offsets(g)==bank_offsets(ng) and bank_offsets(c)==bank_offsets(nc)
assert g[bank_offsets(g)[1]:]==ng[bank_offsets(ng)[1]:]
semantic=lambda cp:[(r['flags'],r['tile'],r['x'],r['y'])for r in cp['parts']]
counts={'raw':0,'non_target_raw':0,'display':0,'non_target_display':0,'target_display':0,'partial_raw_parts_only':0,'gpu_parts':0,'new_boundary_alpha':0};changes=[]
for b in(0,1):
    before,after=graphics_bank(g,b),graphics_bank(ng,b);assert len(before['frames'])==len(after['frames'])
    for f,z in zip(before['frames'],after['frames']):
        n=f['index'];counts['raw']+=1;target=b==0 and n in targets
        assert f['tile_count']==z['tile_count']<=32
        raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,z['offset'],z['limit'],z['tile_count']*128).data
        cp,np_=composition_frame(c,b*5,n),composition_frame(nc,b*5,n)
        if not target:assert raw==nr and semantic(cp)==semantic(np_);counts['non_target_raw']+=1
        if b==1 and n in range(42,50):counts['partial_raw_parts_only']+=1;continue
        a=render(new,b,b*5,n)[0];was=render(old,b,b*5,n)[0]
        assert np.array_equal(a,targets[n]if target else was),(b,n,'display')
        counts['display']+=1
        if not target:counts['non_target_display']+=1;continue
        counts['target_display']+=1;assert np.array_equal(a[masks[n]],was[masks[n]])
        ta=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);tb=np.frombuffer(indexed_atlas(nr,z['tile_count'])[0],np.uint8).reshape(-1,256)
        for q in np_['parts']:
            t=q['tile'];x=t%16*16;y=t//16*16
            if t%16==0:assert not np.any((ta[y:y+16,x]==0)&(tb[y:y+16,x]>0))
            if q['flip_y']and t//16%16==0:assert not np.any((ta[y,x:x+16]==0)&(tb[y,x:x+16]>0))
            counts['gpu_parts']+=1
        changes.append({'ref':n,'changed_display_pixels':int(np.count_nonzero(a!=was))})
assert counts['raw']==444 and counts['non_target_raw']==435 and counts['display']==436 and counts['non_target_display']==427
all_parts=0;composition_changes=[]
allowed_parts={(0,45):{10:(-1,0)},(0,51):{2:(1,0),3:(1,0),4:(1,1)},(0,52):{2:(1,0),3:(1,0),4:(1,1)}}
for b in range(len(bank_offsets(c))):
    count=composition_frame(c,b,0)['bank_frame_count'];assert count==composition_frame(nc,b,0)['bank_frame_count']
    for n in range(count):
        a,z=composition_frame(c,b,n),composition_frame(nc,b,n)
        if semantic(a)!=semantic(z):
            composition_changes.append({'bank':b,'ref':n,'before':semantic(a),'after':semantic(z)})
            assert(b,n)in allowed_parts and len(a['parts'])==len(z['parts'])
            for i,(q,r)in enumerate(zip(a['parts'],z['parts'])):
                dx,dy=allowed_parts[b,n].get(i,(0,0));assert(q['flags'],q['tile'])==(r['flags'],r['tile']) and(r['x'],r['y'])==(q['x']+dx,q['y']+dy)
        else:all_parts+=1
recipe=json.loads((P/'static_effects.json').read_text('utf8'));parent_recipe=json.loads((ROOT/p['source_arc']).with_name('static_effects.json').read_text('utf8'))
assert recipe['parts_sha256']==sha(nc) and {k:v for k,v in recipe.items()if k!='parts_sha256'}=={k:v for k,v in parent_recipe.items()if k!='parts_sha256'}
report={'passed':True,'parent_sha256':sha(old),'candidate_sha256':sha(new),'proposal_sha256':sha((P/'proposal.json').read_bytes()),'source_reconstruction':sources,'shared_body':{'46_48_master':47,'original_variable_pixels':int(variation.sum()),'one_pixel_cape_region':int(region.sum()),'new_body_exact_outside_region':True,'52_original_is_51_dx_minus1':True,'52_new_derived_without_wrap':True},'counts':counts,'changes':changes,'all_other_composition_refs_exact':all_parts,'composition_changes':composition_changes,'bank1_graphics_bytes_exact':True,'non_graphics_entries_exact':other_entries,'palette_audio_timing_exact':True,'head_reference_sha256':sha(head_path.read_bytes()),'static_recipe_sha256':sha((P/'static_effects.json').read_bytes()),'static_recipe_only_parts_hash_rebound':True,'producer_or_packer_called':False,'actual_view_image_files':[str((P/f'{mode}_readback_{i:02}.png').relative_to(ROOT))for mode in('normal','black')for i in range(3)],'visual_notes':['일반·블랙9참조의 재독출6시트를 실제 열람했다. 대기와 같은 머리 및 칼라·소매·허리·부츠의 세부 표현이 이어진다.','46~48은 낮게 웅크린 몸이 동일하고 망토만 변한다. 이 자세의 작은 전체 높이를 캐릭터 크기 축소로 판정하지 않았다.','50의 길게 뻗은 다리와51/52의 종료 자세는 기존 동작 차이를 유지하면서 옷 주름을 보완한다. 원점 시트에서 새 관절 단절이나 새 덩어리화를 발견하지 않았다.'],'limitations':['새 손·발은 원화로 제작했고 원 픽셀 고정 마스크는 없다. hand_contact_exact=None이며 실제 벽면/지면 접촉 검증으로 확대하지 않는다.','bank1 42..49 부분 VRAM 참조는 원시·조립 보존만 검사했다.','MIPS/GPU 및 실제 게임 검사는 루트의 별도 근거다.'],'runtime_verified':False}
O=H/'riko_dash_independent';O.mkdir(exist_ok=True);(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'counts':counts,'composition_changes':composition_changes,'report':str(O/'verification.json')}))
