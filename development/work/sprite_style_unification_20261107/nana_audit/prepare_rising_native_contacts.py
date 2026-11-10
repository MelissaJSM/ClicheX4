"""나나 후속 라이징 원화의 순정 효과/자세/팔레트 기준. 새 그림·게임 쓰기 없음."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
N=Path(__file__).resolve().parent;ROOT=N.parents[2];H=N.parent/'shibuki_audit'
sys.path[:0]=[str(ROOT),str(H)]
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,animation_map
from scripts.export_sprite_playback import parse_sequence
from audit_rising_fire_contact_probe import run
from audit_cyclone_contact import translate
from src.psx_disc import file_hash
sha=lambda b:hashlib.sha256(b).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
def bbox(z):
 yy,xx=np.nonzero(z);return [int(xx.min())-160,int(yy.min())-160,int(xx.max())-159,int(yy.max())-159] if len(xx) else None
def main():
 out=N/'rising_repaint/native_contacts_v1';assert not out.exists();out.mkdir(parents=True)
 us=ROOT/'MegaMan X4.bin';assert file_hash(us)=='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
 assets=read_disc(us,['PL00_U.ARC','SLUS_005.61'])[0];original=Archive(assets['PL00_U.ARC']);exe=assets['SLUS_005.61']
 assert sha(original.data)=='92b2a3209ad6603cf519616dc580400434271f87e8e7129495430c04d0d1c35a'
 paths=[N/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC',N/'ultimate_run_repaint/packed_run_candidate_v1/PL02_U.ARC']
 expected=['cbe6996784a901363abab2d93c81dca49ade8574ac0d5c378af398651f2f6cfa','49da59790a3ad45c6b5a99f78e4786c135d8d017baa67ff55c07373a26f7fbe9']
 arcs=[]
 for p,e in zip(paths,expected):
  data=p.read_bytes();assert sha(data)==e;arcs.append(Archive(data))
 baseline=ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin'
 assert file_hash(baseline)=='f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720'
 current=read_disc(baseline,['SLUS_005.61'])[0]['SLUS_005.61'];off=lambda a:a-0x80010000+2048
 ranges=[(0x80037e4c,0x80037f78),(0x80039570,0x80039860),(0x800951c0,0x800957b0),(0x8010890c,0x80108944),(0x8011ba28,0x8011bb3c),(0x8011c0b0,0x8011c0c8)]
 for lo,hi in ranges:assert exe[off(lo):off(hi)]==current[off(lo):off(hi)]
 cases=[run(exe,original,ch,st,facing) for ch in (False,True) for st in (0,1) for facing in (0,64)]
 for a in arcs:
  for ch in (False,True):
   for st in (0,1):
    for facing in (0,64):
     q=run(current,a,ch,st,facing);match=next(v for v in cases if (v['charged'],v['subtype'],v['facing'])==(ch,st,facing))
     assert q==match
 sequences={str(c['animation']):parse_sequence(exe,0x8011c0b0,c['animation']) for c in cases};effect_rows=[]
 for aid,seq in sequences.items():
  for ref in sorted({s['frame_ref'] for s in seq['steps']}):
   z,meta=original.layer(ref,13,5)
   for a in arcs:assert np.array_equal(a.layer(ref,13,5)[0],z)
   Image.fromarray(z).save(out/f'effect_anim{aid}_{ref:03}.png')
   effect_rows.append({'animation':int(aid),'ref':ref,'bbox_world':bbox(z),'indexed_sha256':sha(z.tobytes()),'opaque':int(np.count_nonzero(z))})
 forms=[('base',arcs[0],0),('fourth',arcs[0],15),('ultimate_before',arcs[1],15),('ultimate_after',arcs[1],0)]
 refs=[100,101,102,103,104,231,232];body_records=[];font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
 def cell(im,label,w=384,h=404):
  c=Image.new('RGB',(w,h),'#263142');pic=im.crop((112,104,208,200)).resize((w,w),Image.Resampling.NEAREST);c.paste(pic,(0,20),pic);ImageDraw.Draw(c).text((5,3),label,font=font,fill='white');return c
 for name,a,mask in forms:
  sheet=Image.new('RGB',(384*4,404*2),'#263142');items=[(0,'idle0')]+[(r,str(r)) for r in refs]
  for i,(n,label) in enumerate(items):
   im=a.composite(n,mask)[0];im.save(out/f'{name}_{n:03}.png');sheet.paste(cell(im,f'{name} / {label}'),(i%4*384,i//4*404))
   body_records.append({'form':name,'ref':n,'RGBA_sha256':sha(im.tobytes()),'bbox':bbox(np.array(im)[:,:,3]>0)})
  sheet.save(out/f'body_{name}.png')
 for st,bodyref in [(0,232),(1,104)]:
  panels=[]
  for name,a,mask in [('original_us',original,0),*forms]:
   for facing in (0,64):
    c=next(v for v in cases if (v['charged'],v['subtype'],v['facing'])==(False,st,facing))
    eff=translate(original.layer(c['initial_ref'],13,5)[0],*c['spawn_world'],c['flip_x'])
    body=np.array(a.composite(bodyref,mask)[0]);moved=np.zeros_like(body);yy,xx=np.nonzero(body[:,:,3]);nx=319-xx if facing else xx;moved[yy,nx]=body[yy,xx]
    overlay=Image.fromarray(moved);cyan=np.zeros_like(moved);cyan[eff>0]=[25,205,220,155];overlay.alpha_composite(Image.fromarray(cyan))
    panels.append(cell(overlay,f'{name} {bodyref} facing{facing} / native effect'))
  board=Image.new('RGB',(768,404*5),'#263142')
  for i,p in enumerate(panels):board.paste(p,(i%2*384,i//2*404))
  board.save(out/f'normal_{bodyref}_native_effect_overlay.png')
 animations,_=animation_map(exe);selected=[q for q in animations if any(s['frame'] in refs for s in q['steps'])]
 relations=[]
 for name,a,mask in forms:
  for x in refs:
   for y in refs:
    if y<=x:continue
    one=np.array(a.composite(x,mask)[0]);two=np.array(a.composite(y,mask)[0])
    for dx,dy in [(0,0),(0,1),(0,-1)]:
     if np.array_equal(np.roll(np.roll(one,dy,0),dx,1),two):relations.append({'form':name,'source':x,'target':y,'translation':[dx,dy],'exact_RGBA':True})
 result={'passed':True,'scope':'현재 나나 4폼 특수7과 원US 라이징 효과의 정적 준비. 원래 초기화 MIPS를24회 실행하고 2현재ARC 원효과와 위치가 동일함을 대조했다.',
  'sources':[{'path':rel(p),'sha256':h}for p,h in zip(paths,expected)],'original_us_bin_sha256':file_hash(us),'original_us_arc_sha256':sha(original.data),
  'original_exe_sha256':sha(exe),'current_baseline_exe_sha256':sha(current),'native_calls':24,'native_initializers':cases,'effect_sequences':sequences,
  'effect_frames':effect_rows,'body_frames':body_records,'original_player_animations':selected,'exact_body_relations':relations,
  'code_ranges_current_original_exact':[list(map(hex,r))for r in ranges],
  'normal_release_refs':{'ground':232,'air':104},'first_generation_priority':[103,104],
  'weapon_requirement':'나나는 권총 사랑이를 유지한다. 원US 주먹만 복제하지 말고 위로 향한 총구·손목·어깨를 원래 불꽃 위치에 자연스럽게 연결한다.',
  'limits':['청록은 원효과 색인이 차지하는 영역을 표시한 진단색이며 실제 CLUT나 실기 화면이 아니다.','차지100..102와 효과의 상대 갱신위상은 이 자료에서 재현하지 않았다.','최초 효과 생성점은 총구 좌표 자체가 아니다. 실제 위쪽 총열/불꽃 접속은 새 그림에서 별도 검수한다.'],
  'new_art_generated':False,'runtime_verified':False,'game_or_pointer_or_save_modified':False}
 (out/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'passed':True,'cases':len(cases),'native_calls':24,'effect_frames':len(effect_rows),'manifest_sha256':sha((out/'manifest.json').read_bytes())}))
if __name__=='__main__':main()
