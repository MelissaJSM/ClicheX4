"""원 hover_jet 코드/정적 타일15와 독립 열람 결론. 원자원 미변경."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
import capstone
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;O=D/'nana_ultimate_hover_relations01'
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import entry
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition,tile_pixels
sha=lambda z:hashlib.sha256(z).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
report=json.loads((O/'report.json').read_text('utf8'));cur=Archive((ROOT/report['candidate_path']).read_bytes())
z,_=read_disc(ROOT/'MegaMan X4.bin',['SLUS_005.61','PL02_U.ARC']);us=Archive(z['PL02_U.ARC']);orig=z['SLUS_005.61']
now,_=read_disc(ROOT/report['current_disc'],['SLUS_005.61']);exe=now['SLUS_005.61'];off=lambda a:a-0x80010000+2048
codes=[];cs=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS32|capstone.CS_MODE_LITTLE_ENDIAN)
for name,lo,hi in(('hover_start',0x80038970,0x800389dc),('hover_jet',0x800b2ad0,0x800b2c8c),('hover_check',0x8003751c,0x800375a8)):
 a=orig[off(lo):off(hi)];b=exe[off(lo):off(hi)];assert a==b
 p=O/(name+'_mips.txt');p.write_text('\n'.join(f'{i.address:08x} {i.mnemonic} {i.op_str}'for i in cs.disasm(b,lo))+'\n','utf8')
 codes.append({'name':name,'start':hex(lo),'end':hex(hi),'original_us_bytes_exact':True,'sha256':sha(b),'disassembly':rel(p)})
static=entry(cur.data,0x10206);ustatic=entry(us.data,0x10206);rows=[];tiles=set();seq=[];items=[]
for n,aid in((221,33),(223,34),(225,35),(227,36),(229,32)):
 address=struct.unpack_from('<I',orig,off(0x8011bf40+aid*4))[0];assert orig[off(0x8011bf40+aid*4):off(0x8011bf40+aid*4+4)]==exe[off(0x8011bf40+aid*4):off(0x8011bf40+aid*4+4)]
 assert orig[off(address):off(address+12)]==exe[off(address):off(address+12)]
 steps=[struct.unpack_from('<bbbB',orig,off(address+i*4))for i in range(3)]
 seq.append({'player_refs':[n,n+1],'effect_animation':aid,'pointer':hex(address),'steps':[list(q)for q in steps],'object_origin_equals_player':True,'object_direction_equals_player':True})
 for _,_,_,r in steps:
  cp=composition_frame(cur.c,12,r);up=composition_frame(us.c,12,r)
  sig=lambda q:(q['flags'],q['tile'],q['x'],q['y'])
  assert[sig(q)for q in cp['parts']]==[sig(q)for q in up['parts']]
  for q in cp['parts']:
   t=q['page']*256+q['tile'];tiles.add(t);assert tile_pixels(static,t)==tile_pixels(ustatic,t)
  px,sz,bb,_=compose_static(static,local_composition(cp));sm=np.frombuffer(px,np.uint8).reshape(sz[1],sz[0]);arr=np.zeros((384,384),np.uint8);arr[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=sm
  np.save(O/f'jet_frame{r:02}.npy',arr);yy,xx=np.nonzero(arr)
  rows.append({'player_refs':[n,n+1],'effect_frame':r,'parts':cp['parts'],'bounds_opaque_world':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],'opaque':len(xx),'indices':np.unique(arr[arr>0]).tolist(),'indexed_sha256':sha(arr.tobytes()),'source_dump':rel(O/f'jet_frame{r:02}.npy'),'original_US_records_and_whole_tiles_exact':True})
  # Neutral index diagnostic: effect palette is runtime-global CLUT0x7802,
  # not the player's body row. Avoid using a guessed body palette.
  im=Image.new('RGBA',(384,384));tab=np.array([[0,0,0,0]]+[[40+i*12,90+i*8,130+i*8,255]for i in range(1,16)],np.uint8);im=Image.fromarray(tab[arr]);body=cur.composite(n,15)[0];im.alpha_composite(body);items.append((f'{n} FX{r} neutral colors',im))
cw,ch=272,316;board=Image.new('RGB',(cw*3,ch*5),'#263345');draw=ImageDraw.Draw(board)
for i,(label,im)in enumerate(items):
 x,y=i%3*cw,i//3*ch;draw.text((x+4,y+3),label,fill='white');im=im.crop((128,124,192,194)).resize((256,280),Image.Resampling.NEAREST);board.paste(im,(x+8,y+26),im)
board.save(O/'all15_original_jet_phases.png')
hist=Archive((ROOT/report['historical_aligned_arc']).read_bytes());low=[]
for pair in report['pairs']:
 n=pair['refs'][0];cut=160+pair['historical_cut_world_y'];a=np.array(cur.composite(n,15)[0]);b=np.array(hist.composite(n,15)[0]);low.append({'ref':n,'world_cut_y':cut-160,'old_aligned_lower_RGBA_exact':np.array_equal(a[cut:],b[cut:]),'different_lower_cells':int(np.any(a[cut:]!=b[cut:],axis=2).sum())})
inputs={rel(ROOT/'scripts/ultimate_costume_swap.py'):sha((ROOT/'scripts/ultimate_costume_swap.py').read_bytes())}
for p in('player_special.c','player_weapon.c','object_update.c'):
 q=ROOT/'work/research/decomp/src/main'/p;inputs[rel(q)]=sha(q.read_bytes())
for q in(ROOT/'work/research/decomp/config/symbols.us.txt',):inputs[rel(q)]=sha(q.read_bytes())
out={'passed':True,'parent_report':rel(O/'report.json'),'parent_report_sha256':sha((O/'report.json').read_bytes()),'code':codes,'static_jet_composition_bank':12,'static_texture_entry':'0x10206','global_effect_CLUT':'0x7802; 몸 팔레트로 대신하지 않음','effect_sequences':seq,'effect_frames':rows,'whole_tiles':[{'tile':t,'sha256':sha(tile_pixels(static,t)),'original_us_exact':True}for t in sorted(tiles)],'lower_historical_comparison':low,'inputs':inputs,'conclusions':['현재 10참조는 5개 사격짝 raw를 공유하고 하체5층은 각 짝에서 exact, 다른6/7/8층은 투명이다. layer5는 다리이며 재킷/불꽃이 아니다.','현재 RN36의 Ultimate renderer는217..230에 항상 mask15. 캡슐 전은 기술 도달성이 별도이며 mask0 그림만으로 신체 누락을 판단하면 안 된다.','원US visual0x21은 별도 객체이며 update0x800B2AD0..2C8C에서 매 tick 플레이어 x/y/방향을 그대로 복사한다. 추가 위치 offset은 없다. effect 조립은행12와 원시 정적텍스처0x10206을 사용하고, 플레이어221..230의 bank0/body타일에서 불꽃을 만들지 않는다.','원효과 animation33/34/35/36/32가 각각221쌍/223쌍/225쌍/227쌍/229쌍이다. 각3phase/1call 순환, 총15frame의 원파트와 실제소비6타일(504..509)을 독립 대조했다.','새 발은 원효과15 phase와 원점 동일 합성으로 확인할 것. 과거 jets PNG는 일부색/가림이 빠진 정적 추출이며 전체효과 마스크의 대용이 아니다.','11/04 상체 공중39/37/45/47/41 재사용과 하체등록은 당시 제작정책이다. 최신공중 원화를 무조건 같은 좌표로 복사하는 근거가 아니다.'], 'actually_viewed':['current_layers_00.png','current_layers_01.png','current_layers_02.png','historical_jets.png'],'neutral_effect_board_actually_viewed':False,'runtime_executed':False,'new_MIPS_execution':False,'new_art_acceptance':False,'producer_functions_called':False}
(O/'conclusions.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'sha256':sha((O/'conclusions.json').read_bytes()),'tiles':sorted(tiles),'lower':low},ensure_ascii=False))
