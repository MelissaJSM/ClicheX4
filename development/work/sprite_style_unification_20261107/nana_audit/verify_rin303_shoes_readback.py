"""린303 초기 기술감사 위 신발4 색변경만 별도 독립 대조."""
from pathlib import Path
import sys,json,hashlib,struct,collections
import numpy as np
from PIL import Image
N=Path(__file__).resolve().parent;ROOT=N.parents[2];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets
from src.psx_frame_edit import frame_coverage
D=ROOT/'work/sprite_style_unification_20261107/zero_audit/rin_extension';sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
def raw(g,f):return decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
def main():
 prior=N/'rin303_independent_readback.json';assert sha(prior.read_bytes())=='2ab41fc50e68bbce7f564fedeaeff48c19323c7eb8162604db07ad34216a917b'
 old=(D/'prepared_burst_remaining01/PL01_U.ARC').read_bytes();new=(D/'prepared_burst_remaining02/PL01_U.ARC').read_bytes()
 assert sha(old)=='626a059f3a290d5d15f647aa6bbb8b9be51e88060638d6a14d62a34508835f6a'
 assert sha(new)=='1dde3e8793628d5f38b4318543e8d9f3a22b37ad350622a96f4f4f63e92610b9'
 g,ng,c=entry(old,2),entry(new,2),entry(old,3);assert replace_entry(new,2,g)==old
 assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)
 art=D/'burst_shoe_edit01/generated.png';assert sha(art.read_bytes())=='ddd35dc51e12faa45cfb4048c7ab17798b0058bcbe5bd463b673220b47a62069'
 im=Image.open(art).convert('RGBA');assert im.size==(1536,1024);imarr=np.array(im);words=struct.unpack_from('<16H',entry(old,9));pal=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in words[1:]],np.int32)
 labels=np.empty(imarr.shape[:2],np.uint8)
 for y in range(im.height):labels[y]=1+((imarr[y,:,:3].astype(np.int32)[:,None]-pal[None])**2).sum(2).argmin(1)
 votes=np.stack([np.array(Image.fromarray(np.where(labels==i,imarr[:,:,3],0).astype(np.uint8)).resize((192,128),Image.Resampling.BOX))for i in range(1,16)])
 alpha=np.array(im.getchannel('A').resize((192,128),Image.Resampling.BOX));full=np.where(alpha>=128,1+votes.argmax(0),0).astype(np.uint8)
 inputs=read(D/'burst_charge01/inputs.json');reg=read(D/'burst_charge_registered_v1/registration.json');newreg=read(D/'burst_charge_registered_v2/registration.json')
 Y,X=np.indices((384,384));perstream={};records=[];fs=graphics_bank(g,1)['frames']
 for q in inputs['masters']:
  n=q['ref'];cx,cy=q['cell'];x0,y0,x1,y1=q['world_crop'];source=np.zeros((384,384),np.uint8);source[y0:y1,x0:x1]=full[cy*64:(cy+1)*64,cx*96:(cx+1)*96]
  dx,dy=next(r for r in reg['records']if r['ref']==n)['whole_body_translation'];source=np.roll(source,(dy,dx),(0,1))
  body=np.array(Image.open(D/'burst_charge_registered_v1'/f'b1_{n:03}_body_indices.png'))
  valid=(Y>=173+dy)&(X>=130)&(X<193)&np.isin(body,(2,3,4,7,8))&np.isin(source,(4,5,6))
  target=body.copy();target[valid]=source[valid];changed=target!=body
  assert np.array_equal(target>0,body>0) and np.array_equal(target[body==1],body[body==1]) and np.array_equal(target[np.isin(body,(9,10,11))],body[np.isin(body,(9,10,11))])
  regrec=next(r for r in newreg['records']if r['ref']==n);p=D/'burst_charge_registered_v2'/f'b1_{n:03}_body_indices.png';assert sha(p.read_bytes())==regrec['target_sha256'];assert np.array_equal(target,np.array(Image.open(p)))
  fx=np.array(Image.open(D/'burst_remaining_probe01'/f'b1_{n:03}_effect_indices.png'));target[fx>0]=fx[fx>0]
  before=render(old,1,5,n)[0];after=render(new,1,5,n)[0];assert np.array_equal(after,target) and np.array_equal(before>0,after>0)
  actual=before!=after;assert np.count_nonzero(actual)==[34,41,37,42][n-178];assert not np.any(actual&(fx>0))
  f=fs[n];rr=raw(g,f);cp=composition_frame(c,5,n);cov,size,bb=frame_coverage(rr,f['tile_count'],cp);allowed=perstream.setdefault(f['offset'],set())
  for yy,xx in np.argwhere(actual):allowed.update(cov[(yy-160-bb[1])*size[0]+xx-160-bb[0]])
  records.append({'ref':n,'changed_index_pixels':int(actual.sum()),'actual_source_same_coordinate_blue_exact':True,'alpha_contour_white_highlights_exact':True})
 counts=collections.Counter()
 for b in (0,1):
  of,nf=graphics_bank(g,b)['frames'],graphics_bank(ng,b)['frames']
  for f,h in zip(of,nf):
   n=f['index'];assert f['tile_count']==h['tile_count'];rr,nr=raw(g,f),raw(ng,h);counts['raw_checked']+=1
   if rr==nr:counts['raw_exact']+=1
   else:
    assert b==1 and f['offset'] in perstream
    for i in range(len(rr)*2):
     byte,shift=i//2,i%2*4
     if (rr[byte]>>shift&15)!=(nr[byte]>>shift&15):assert (byte,shift) in perstream[f['offset']]
   assert composition_frame(c,b*5,n)==composition_frame(entry(new,3),b*5,n)
   if b==1 and 42<=n<=49:assert rr==nr;counts['partial8_exact']+=1;continue
   before,after=render(old,b,b*5,n)[0],render(new,b,b*5,n)[0];assert np.array_equal(before>0,after>0);counts['display_checked']+=1
   if not (b==1 and n in range(178,182)):assert np.array_equal(before,after);counts['non_target_display_exact']+=1
 assert counts['raw_checked']==444 and counts['non_target_display_exact']==432 and sum(q['changed_index_pixels']for q in records)==154
 j={'passed':True,'prior_independent_report':prior.relative_to(ROOT).as_posix(),'prior_report_sha256':sha(prior.read_bytes()),'source_candidate_sha256':sha(old),'candidate_sha256':sha(new),
  'generated_shoe_source_sha256':sha(art.read_bytes()),'source_color_reconstructed_independently':True,'producer_functions_called':False,'records':records,'counts':dict(counts),
  'all_composition_palette_other_entries_exact':True,'all_display_alpha_exact':True,'original_effect_pixels_1064_exact_via_parent_and_increment':True,
  'visual_review_performed':False,'root_art_acceptance_verified_here':False,'runtime_verified':False,'native_cpu_run_performed':False,
  'scope':'초기303 기술감사에 색교정4참조를 추가한 독립 읽기. 원화의 고정1/8 팔레트 투표와 동일좌표 blue4/5/6을 직접 재구성해154색인만 바뀜을 확인. 미술수용·새MIPS·실기는 별도.'}
 out=N/'rin303_shoes_independent_readback.json';out.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(counts),'report_sha256':sha(out.read_bytes())}))
if __name__=='__main__':main()
