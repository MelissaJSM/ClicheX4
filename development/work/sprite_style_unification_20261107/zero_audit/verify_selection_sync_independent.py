"""제작 패커를 호출하지 않고 Zero 선택 전신 사본과 비대상/반전 의미를 읽어 검사한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import psx_arc
from scripts.overhaul_sprites_audit import render
from src.psx_player import composition_frame,bank_offsets
W=ROOT/'work/sprite_style_unification_20261107';O=Path(__file__).parent/'selection_sync_independent01';O.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
mapping={0:(0,147),**{n:(0,n+60)for n in(1,2,3,5,7,9,11,13,15,17,19,21)},22:(0,82),23:(0,131),24:(0,132),25:(0,133),26:(0,134),**{n:(1,n-27)for n in range(27,41)}}
def tile(tex,t):
 a=np.zeros((16,16),np.uint8)
 for y in range(16):
  for x in range(16):
   off=(t//16*16+y)*128+t%16*8+x//2;a[y,x]=(tex[off]>>(4*(x%2)))&15
 return a
def static(tex,parts,bank,n):
 a=np.zeros((384,384),np.uint8);c=composition_frame(parts,bank,n)
 for p in c['parts']:
  z=tile(tex,p['page']*256+p['tile'])
  if p['flip_x']:z=z[:,::-1]
  if p['flip_y']:z=z[::-1]
  x,y=160+p['x'],160+p['y'];view=a[y:y+16,x:x+16];nz=z>0;view[nz]=z[nz]+p['clut']*16
 return a,c
results={}
for char,mode in [('riko','br'),('rin','rn')]:
 folder=W/'selection_sync01'/char;report=json.loads((folder/'report.json').read_text('utf8'));plan=json.loads((W/f'staging_{mode}_v12.json').read_text('utf8'));inp=json.loads((folder/'integration_candidate.json').read_text('utf8'))
 source=ROOT/report['source_bin'];assert sha(source.read_bytes())==report['source_sha256'];assets,_=read_disc(source,('ST0E_U1.ARC','COL0E_U1.ARC'))
 old=assets['ST0E_U1.ARC']
 if 'ST0E_U1.ARC'in plan['resources']:old=(ROOT/plan['resources']['ST0E_U1.ARC']['path']).read_bytes()
 assert sha(old)==report['source_selection_sha256'];new=(folder/'ST0E_U1.ARC').read_bytes();assert sha(new)==report['candidate_sha256']
 bp=ROOT/inp['resources']['PL01_U.ARC']['path'];body=bp.read_bytes();assert sha(body)==report['body_sha256'];assert len(new)==len(old)
 ot,nt=entry(old,0x10102),entry(new,0x10102);op,np_=entry(old,10),entry(new,10);assert nt[40960:]==ot[40960:];assert len(op)==len(np_)
 offsets=struct.unpack('<3I',entry(old,12));assert offsets==(0,40960,90112)and entry(old,12)==entry(new,12)
 for e in psx_arc(old):
  if int(e['type'],16)not in(10,0x10102):assert new[e['offset']:e['offset']+e['size']]==old[e['offset']:e['offset']+e['size']]
 # Preserve directory/header bytes and every non-target record; target geometry
 # may be re-registered, but part count is fixed and final world origin exact.
 oo,no=bank_offsets(op),bank_offsets(np_);assert oo==no;assert op[:oo[0]]==np_[:no[0]]
 target_offsets=set();owned=set();reserved=set(range(320));total=0;other=0;target=0;flip_records=[];gpu=0;changed=[]
 for bank in range(len(oo)):
  count=composition_frame(op,bank,0)['bank_frame_count'];assert count==composition_frame(np_,bank,0)['bank_frame_count']
  assert op[oo[bank]:oo[bank]+count*4]==np_[no[bank]:no[bank]+count*4]
  for n in range(count):
   start=offsets[bank];end=offsets[bank+1]if bank+1<len(offsets)else len(ot)
   before,bc=static(ot[start:end],op,bank,n);after,ac=static(nt[start:end],np_,bank,n);assert len(bc['parts'])==len(ac['parts']);total+=1
   if bank==0 and n in mapping:
    target+=1;gb,ref=mapping[n];wanted=render(body,gb,gb*5,ref)[0];assert np.array_equal(after%16,wanted),f'{char} body {n}';assert np.all(after[after>0]<16),f'{char} CLUT {n}'
    if not np.array_equal(before,after):changed.append(n)
    for p,q in zip(bc['parts'],ac['parts']):
     owned.add(p['page']*256+p['tile']);target_offsets.update(range(q['record_offset'],q['record_offset']+4));t=q['page']*256+q['tile'];z=tile(nt,t)
     # The PS1 UV endpoint wraps at tile column0 and page top. The
     # producer reserves transparent border texels, including newly mirrored records.
     if t%16==0:assert not z[:,0].any(),f'{char} firstcol {n}'
     if t%256<16:assert not z[0].any(),f'{char} firstrow {n}'
     gpu+=1
     if (p['flags']^q['flags'])&0xc0:flip_records.append({'frame':n,'record':q['record_offset'],'old_flags':p['flags'],'new_flags':q['flags'],'tile':t})
   else:
    assert np.array_equal(before,after);other+=1
    for p,q in zip(bc['parts'],ac['parts']):assert op[p['record_offset']:p['record_offset']+4]==np_[q['record_offset']:q['record_offset']+4]
 for bank in (0,):
  for n in range(composition_frame(op,bank,0)['bank_frame_count']):
   if bank==0 and n in mapping:continue
   for p in composition_frame(op,bank,n)['parts']:
    t=p['page']*256+p['tile']
    if t<320:owned.discard(t)
 reserved-=owned
 for t in reserved:assert np.array_equal(tile(ot,t),tile(nt,t))
 assert all(a==b or i in target_offsets for i,(a,b)in enumerate(zip(op,np_)))
 assert entry(assets['COL0E_U1.ARC'],5)[:32]==entry(body,9)[:32]
 results[char]={'passed':True,'source_bin_sha256':report['source_sha256'],'source_selection_sha256':sha(old),'candidate_sha256':sha(new),'body_sha256':sha(body),'total_static_frames':total,'target_body_copies':target,'changed_copies':changed,'non_target_static_frames_exact':other,'palette_exact':True,'portrait_and_X_texture_exact':True,'all_other_entries_exact':True,'non_owned_tiles_exact':len(reserved),'target_GPU_parts_checked':gpu,'flipped_records':flip_records,'world_pixels_origin_and_normal_RGBA_exact':True,'all_part_counts_and_headers_exact':True,'all_non_target_part_bytes_exact':True,'producer_patch_or_pack_called':False,'runtime_verified':False}
out={'passed':True,'projects':results,'scope':'두 선택창 Zero 전신 사본만 실제 최신 PL01 픽셀/원점에 동기화됐는지 독립 읽기 검사. 정상 팔레트와 반전 texel/파트 의미 및 GPU 경계 투명값을 대조했습니다. 미술 열람과 실제 게임은 별도입니다.'}
(O/'report.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({k:{q:v[q]for q in('candidate_sha256','target_body_copies','non_target_static_frames_exact','non_owned_tiles_exact','target_GPU_parts_checked')}for k,v in results.items()}))
