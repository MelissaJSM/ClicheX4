"""원US/RN36 호버 총구표·일반탄 첫 효과를 읽는 정적 감사. 실행/자원변경 없음."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
import capstone
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,animation_map
from scripts.prepare_riko_ui import entry
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition,tile_pixels
O=D/'nana_ultimate_hover_muzzle01';O.mkdir(exist_ok=False)
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();off=lambda a:a-0x80010000+2048
orig,_=read_disc(ROOT/'MegaMan X4.bin',['SLUS_005.61','PL02_U.ARC'])
disc=ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v36/rin_nana.bin'
now,_=read_disc(disc,['SLUS_005.61','PL02_U.ARC']);oe,ce=orig['SLUS_005.61'],now['SLUS_005.61'];ua,na=Archive(orig['PL02_U.ARC']),Archive(now['PL02_U.ARC'])
cs=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS32|capstone.CS_MODE_LITTLE_ENDIAN);codes=[]
for name,lo,hi in [('muzzle',0x80092e2c,0x80092f08),('follow',0x80092cec,0x80092d64),('lemon_init_launch',0x80092314,0x800924f8),('shoot_animation',0x80038524,0x800385ec),('hover_main',0x800388f0,0x80038970),('shoot_air',0x80037338,0x800373d8)]:
 ob,cb=oe[off(lo):off(hi)],ce[off(lo):off(hi)];assert ob==cb
 p=O/(name+'_mips.txt');p.write_text('\n'.join(f'{i.address:08x} {i.mnemonic} {i.op_str}'for i in cs.disasm(cb,lo))+'\n','utf8')
 codes.append({'name':name,'range':[hex(lo),hex(hi)],'original_us_bytes_exact':True,'sha256':sha(cb),'disassembly':rel(p)})
refs=(222,224,226,228,230);origins=[]
for n in refs:
 a,b=oe[off(0x8011b230+n*2):off(0x8011b230+n*2+2)],ce[off(0x8011b230+n*2):off(0x8011b230+n*2+2)];assert a==b
 origins.append({'ref':n,'offset_table_address':hex(0x8011b230+n*2),'direction0_xy':list(struct.unpack('<bb',a)),'direction1_xy':[-struct.unpack('<b',a[:1])[0],struct.unpack('<b',a[1:])[0]],'original_current_exact':True})
types=[]
for n in range(24):
 q=off(0x80108768+n*4);assert oe[q:q+4]==ce[q:q+4]
 types.append({'type':n,'xy16':list(struct.unpack_from('<hh',oe,q))})
seqp=struct.unpack_from('<I',oe,off(0x8011bf40+21*4))[0];assert oe[off(seqp):off(seqp+28)]==ce[off(seqp):off(seqp+28)]
steps=[list(struct.unpack_from('<bbbB',oe,off(seqp+i*4)))for i in range(7)]
ut,nt=entry(ua.data,0x10206),entry(na.data,0x10206);fx=[];arrays=[]
def signature(c):return[(q['flags'],q['tile'],q['x'],q['y'])for q in c['parts']]
for _,_,_,n in steps:
 u=composition_frame(ua.c,1,n);v=composition_frame(na.c,1,n);assert signature(u)==signature(v)
 tiles=sorted({q['page']*256+q['tile']for q in u['parts']})
 for t in tiles:assert tile_pixels(ut,t)==tile_pixels(nt,t)
 b,s,box,_=compose_static(ut,local_composition(u));z=np.frombuffer(b,np.uint8).reshape(s[1],s[0]);whole=np.zeros((384,384),np.uint8);whole[160+box[1]:160+box[3],160+box[0]:160+box[2]]=z;arrays.append(whole)
 yy,xx=np.nonzero(whole);fx.append({'frame':n,'opaque':len(xx),'opaque_bbox_inclusive':[int(xx.min()-160),int(yy.min()-160),int(xx.max()-160),int(yy.max()-160)],'indexed_sha256':sha(whole.tobytes()),'original_current_whole_tiles_exact':True,'parts':u['parts'],'tiles':tiles})
np.save(O/'lemon_first_frame.npy',arrays[0])
U=W/'nana_audit/ultimate_hover_repaint/shot_joint_probe_v1';inputs={};rows=[];items=[]
def bounds(z):
 yy,xx=np.nonzero(z);return None if not len(xx)else[int(xx.min()-160),int(yy.min()-160),int(xx.max()-160),int(yy.max()-160)]
for i,n in enumerate(refs):
 x,y=origins[i]['direction0_xy'];effect=np.roll(np.roll(arrays[0],y,axis=0),x,axis=1)
 p=U/f'body_{n}_indices.png';inputs[rel(p)]=sha(p.read_bytes());nz=np.asarray(Image.open(p));ni=na.rgba(nz,16)
 allb=[('original US',ua.composite(n,15)[0]),('RN36 old Nana',na.composite(n,15)[0]),('new static candidate',ni)]
 yy,xx=np.indices((384,384));gx=(-22,-23,-22,-22,-22)[i]
 gate=(xx>=160+gx)&(xx<160+gx+8)&(yy>=160-15)&(yy<=160-5)
 ro={'ref':n,'engine_origin_xy':[x,y],'first_flash_world_bbox':bounds(effect),'first_flash_note':'원색인/알파이며 판에서는 중립 노랑으로 표시. 원게임 팔레트나 draw-order 합성 캡처가 아님.','images':[]}
 for title,body in allb:
  b=np.array(body);al=b[:,:,3]>0
  ro['images'].append({'label':title,'first_flash_overlap_all_body':int(((effect>0)&al).sum()),'first_flash_overlap_diagnostic_gun_window':int(((effect>0)&al&gate).sum())})
  canvas=Image.new('RGBA',(384,384));fi=np.zeros((384,384,4),np.uint8);fi[effect>0]=(255,210,20,130);canvas.alpha_composite(Image.fromarray(fi));canvas.alpha_composite(body)
  dr=ImageDraw.Draw(canvas);dr.line((x+159,y+160,x+161,y+160),fill='#00eeff');dr.line((x+160,y+159,x+160,y+161),fill='#00eeff')
  items.append((f'{n} {title}; origin({x},{y})',canvas))
 rows.append(ro)
cw,ch=394,370;board=Image.new('RGB',(cw*3,ch*5),'#263345');dr=ImageDraw.Draw(board)
for i,(text,img)in enumerate(items):
 x,y=i%3*cw,i//3*ch;dr.text((x+5,y+5),text,fill='white');v=img.crop((118,125,195,193)).resize((385,340),Image.Resampling.NEAREST);board.paste(v,(x+4,y+26),v)
board.save(O/'first_flash_static_comparison.png')
an,ar=animation_map(ce);uan,uar=animation_map(oe);ids=sorted({v for n in refs for v in ar[n]});sequences=[q for q in an if q['id']in ids]
for q in sequences:assert q==uan[q['id']]
report={'scope':'호버 사격5의 실제 원US/RN36 탄환 원점·첫 일반탄 효과 정적 읽기','original_exe_sha256':sha(oe),'current_disc':rel(disc),'current_exe_sha256':sha(ce),'current_arc_sha256':sha(na.data),'codes':codes,'muzzle_formula':'방향0: player+(signed8 refXY + signed8 shotType가 가리키는16bit offset). 방향1: X부호 반전/Y그대로. 원MIPS는 하위16bit 덧셈을 사용한다.','frame_offset_table':'0x8011B230','type_offset_table':'0x80108768','origins':origins,'type_offsets_read':types,'lemon_call_chain':'80092380 초기화→80092CEC follow→80092D4C→80092E2C. launch 첫 단계도800924B0에서follow 재호출. shot+1 subtype을a2로 사용.','animation21_pointer':hex(seqp),'first7_steps':steps,'static_composition_bank':1,'static_texture_entry':'0x10206','actual_effect_CLUT':'0x7802; 진단판은 중립색','first7_effect_frames':fx,'static_contact_diagnostics':rows,'hover_shot_animation_ids':ids,'hover_shot_sequences_original_exact':sequences,'shooting_animation_rule':'unk2==0 및attacking!=0이면 기존21..26에0x70을더함. continue_animation은 event인덱스·duration을보존. 일반탄은별도weapon pose전환 없이hover를이어감.','input_png_hashes':inputs,'conclusions':['현재 그림의8열 총끝 보호는 원점표와 일치 증거가 아니다. 원점은222(-27,-9),224(-29,-8),226(-20,-10),228(-17,-10),230(-24,-11)로 각기 다르다.','첫 일반탄 효과는 원점기준x−7..+6/y−10..+9의188픽셀이라 총끝 좌표차이만으로 단절을 단정할 수 없다. 7개 효과 단계 전체 조립·타일을 원US와 대조했다.','cyan 십자는실제 원점표의 위치이고 노란면은원효과 첫188픽셀의중립색 진단이다. 새손/총 정합은 총과첫효과/발사후움직임을 함께 판단해야 한다.','탄환형태·속도·원코드·시간표를 바꾸는 근거가 아니다.'], 'actually_viewed':False,'new_MIPS_execution':False,'runtime_executed':False,'candidate_accepted':False,'producer_functions_called':False}
p=O/'report.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'report_sha256':sha(p.read_bytes()),'origins':origins,'contact':rows}))
