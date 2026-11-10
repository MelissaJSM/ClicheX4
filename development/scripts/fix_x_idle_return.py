"""등장 마지막 ref142를 승인된 idle0 픽셀에 연결하는 자원 전용 교정.

그림/압축 본문/타이밍은 수정하지 않는다. 다른 제작안 뒤 순차 적용할 때는
명시한 input SHA와 원본의 0/141/142 의미 보존 검사를 모두 통과해야 한다.
"""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,TASK,OUT,SOURCES,sha,digest,write,need,relative,FONT,read,animation_map
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import bank_offsets,composition_frame

D=TASK/'idle_return_fix/prepared_v1'
INPUTS={('shibuki','PL00_U.ARC'):'b29e6336a813ce388a36a2966b1fd50f0fccd054ded5520167e271fc11572e2b',
 ('shibuki','PL02_U.ARC'):'c9ae26c9e187924d21330a2b9218427db633127373b27925719bae2e828fa8c9',
 ('nana','PL02_U.ARC'):'95fb95389330015dddc92091654b4c8559a909384d7957d56897c82c10356ecf'}
PART_BANKS=(0,5,6,7,8)
UNRESOLVED=(105,*range(175,183))

def patch_return_idle(data,baseline,character,name,*,expected_input_sha=None):
 need((character,name) in INPUTS,'교정 범위 밖 자원')
 need(sha(baseline)==INPUTS[character,name],'지원하지 않는 기준 자원')
 need(sha(data)==(expected_input_sha or INPUTS[character,name]),'지원하지 않는 입력 자원')
 ref=Archive(baseline);before=Archive(data)
 need(len(data)==len(baseline),'ARC 크기 변경')
 need(before.p==ref.p,'팔레트 변경과 함께 처리할 수 없음')
 need(bank_offsets(before.g,allow_aliases=True)==bank_offsets(ref.g,allow_aliases=True),'그래픽 경계 변경')
 need(bank_offsets(before.c)==bank_offsets(ref.c),'조립 경계 변경')
 for n in(0,141,142):
  for b in PART_BANKS:
   a,am=before.layer(n,b);r,rm=ref.layer(n,b)
   need(np.array_equal(a,r) and am['decoded_sha256']==rm['decoded_sha256'],'승인 기준 0/141/142가 이미 변경됨')
   # A prior independent patch may repack composition, hence no absolute offsets.
   def parts(meta):return [{k:v for k,v in p.items() if k not in('index','record_offset')} for p in meta['parts']]
   need(parts(am)==parts(rm),'보호 대상 조립 변경')
 offsets=bank_offsets(before.c)
 need([b for b,v in enumerate(offsets) if struct.unpack_from('<I',before.c,v)[0]>>16>142]==list(PART_BANKS),'다른 조립 뱅크의142 공유 확인 필요')
 g=bytearray(before.g);c=bytearray(before.c);ranges=[]
 base=before.banks[0]['base'];at=base+142*4;g[at:at+4]=g[base:base+4];ranges.append({'entry':2,'start':at,'length':4})
 for b in PART_BANKS:
  base=offsets[b];at=base+142*4;c[at:at+4]=c[base:base+4];ranges.append({'entry':3,'bank':b,'start':at,'length':4})
 g,c=bytes(g),bytes(c);result=replace_entry(replace_entry(data,2,g),3,c);after=Archive(result)
 need(replace_entry(replace_entry(result,2,before.g),3,before.c)==data,'비대상 entry 변경')
 for entry_id,old,new in((2,before.g,g),(3,before.c,c)):
  allowed={p for r in ranges if r['entry']==entry_id for p in range(r['start'],r['start']+4)}
  need(all(x==y or p in allowed for p,(x,y) in enumerate(zip(old,new))),'24바이트 참조 밖 변경')
 need(g[before.banks[0]['base']+237*4:]==before.g[before.banks[0]['base']+237*4:],'압축 본문 변경')
 checks=0
 for n in range(237):
  if n in UNRESOLVED:continue
  for b in PART_BANKS:
   expected,_=before.layer(0 if n==142 else n,b);actual,_=after.layer(n,b)
   need(np.array_equal(actual,expected),f'조립 회귀 {n}/{b}');checks+=1
 composite_checks=[]
 for arm in(1,2):
  for mask in range(16):
   old,_=before.composite(142,mask,arm);goal,_=before.composite(0,mask,arm);new,_=after.composite(142,mask,arm)
   need(new.tobytes()==goal.tobytes(),'142가 대기0과 다름')
   composite_checks.append({'mask':mask,'arm':arm,'changed_pixels':int(np.any(np.array(old)!=np.array(new),axis=2).sum()),'equals_idle':True})
 need(any(r['changed_pixels'] for r in composite_checks),'이미 교정된 입력')
 return result,{'input_sha256':sha(data),'output_sha256':sha(result),'allowed_reference_ranges':ranges,
  'changed_bytes':sum(x!=y for x,y in zip(data,result)),'indexed_layer_checks':checks,
  'mask142_checks':composite_checks,'all_other_refs_pixel_exact':True,'ref141_exact':True,
  'compressed_body_exact':True,'all_other_entries_palette_and_timing_exact':True,
  'unresolved_refs_preserved_bytes':list(UNRESOLVED),'runtime_verified':False}

def preview(before,after,path,title):
 boxes=[a.composite(n,m)[0].getbbox() for a,n in((before,141),(before,142),(after,142),(after,0)) for m in(0,15)];boxes=[b for b in boxes if b]
 box=(min(b[0] for b in boxes)-3,min(b[1] for b in boxes)-3,max(b[2] for b in boxes)+3,max(b[3] for b in boxes)+3)
 scale=4;w,h=(box[2]-box[0])*scale,(box[3]-box[1])*scale
 board=Image.new('RGB',(w*4,h*2+66),(32,37,49));draw=ImageDraw.Draw(board)
 for j,mask in enumerate((0,15)):
  for i,(a,n,label) in enumerate(((before,141,'141 보존'),(before,142,'142 이전'),(after,142,'142 교정'),(after,0,'대기 0'))):
   im,_=a.composite(n,mask);bbox=im.getbbox();need(not bbox or all((bbox[0]>=box[0],bbox[1]>=box[1],bbox[2]<=box[2],bbox[3]<=box[3])),'비교 시트 잘림')
   x,y=i*w,j*(h+33);draw.text((x+5,y+3),f'{title} mask{mask} {label}',font=FONT,fill='white');im=im.crop(box).resize((w,h),Image.Resampling.NEAREST);board.paste(im,(x,y+30),im)
 board.save(path)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');args=parser.parse_args();need(args.prepare,'--prepare 필요')
 need(not D.exists(),'기존 준비물 덮어쓰기 거부');prepared=[];proof=[]
 for character in('shibuki','nana'):
  source,assets,records=read(character);animations,_=animation_map(assets['SLUS_005.61']);a=animations[2]
  need(a['steps'][-2]=={'position':16,'duration_ticks':33,'event':0,'relative_step':1,'frame':142} and a['steps'][-1]['frame']==142 and a['steps'][-1]['relative_step']==0,'등장 종료 시퀀스 변경')
  files={}
  for name in('PL00_U.ARC','PL02_U.ARC'):
   if (character,name) not in INPUTS:continue
   data=assets[name];result,p=patch_return_idle(data,data,character,name);path=D/character/name
   files[name]={'before':sha(data),'after':sha(result),'size':len(result),'path':relative(path),'record':records[name]}
   prepared.append((path,result,data,character,name));proof.append({'character':character,'file':name,**p})
  folder=D/character;proposal={'project':SOURCES[character][0],'baseline':relative(source),'baseline_sha256':SOURCES[character][2],'files':files,'runtime_verified':False,'semantic_integration':'다른 gfx 패킹 뒤 patch_return_idle 호출. 전체 gfx bank diff 병합 금지.'}
  prepared.append((folder/'proposal.json',proposal,None,character,None));need(digest(source)==SOURCES[character][2],'입력 BIN 변경')
 D.mkdir(parents=True)
 for path,result,old,character,name in prepared:
  path.parent.mkdir(parents=True,exist_ok=True)
  if isinstance(result,dict):write(path,result)
  else:path.write_bytes(result);preview(Archive(old),Archive(result),path.with_suffix('.comparison.png'),f'{character} {name[:4]}')
 write(D/'verification.json',{'passed':True,'assets':proof,'animation2_final142_duration':33,'event140_restores_armor':True,'transition_evidence':'work/research/decomp/src/main/player.c:125..157; actual EXE animation2 bytes','byte_stream_unchanged':True,'runtime_verified':False})
 print('3 resources prepared; compressed bodies and all non142 poses exact')

if __name__=='__main__':main()
