"""읽은 원US 실제 명령/점프표와 네 비교판 관찰을 별도 기록."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;B=D.parent;O=D/'shibuki_standing_special_relations01'
sys.path[:0]=[str(ROOT),str(D)]
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from verify_shibuki_ultimate_hurt13_independent import render,parts
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
rp=O/'report.json';j=json.loads(rp.read_text('utf8'))
a,_=read_disc(ROOT/'MegaMan X4.bin',('SLUS_005.61','PL00_U.ARC'))
exe=a['SLUS_005.61'];base=struct.unpack_from('<I',exe,24)[0];at=lambda addr,n:exe[addr-base+2048:addr-base+2048+n]
jumpbase=0x80010444;targets=struct.unpack('<15I',at(jumpbase,60));expected={2:0x800374c4,11:0x800374c4,12:0x800374d4,4:0x800374e4,13:0x800374f4,7:0x80037504,16:0x80037504}
assert all(targets[k-2]==v for k,v in expected.items())
assert all(v==expected.get(k,0x8003750c) for k,v in enumerate(targets,2))
curp=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v20/shibuki_riko.bin';cu,_=read_disc(curp,('SLUS_005.61',));cur=cu['SLUS_005.61']
blocks=[]
for b in j['native_blocks']:
 st,en=int(b['start'],16),int(b['end'],16);assert at(st,en-st)==cur[st-base+2048:en-base+2048];blocks.append(b['name'])
assert at(jumpbase,60)==cur[jumpbase-base+2048:jumpbase-base+2108]
for q in j['tables']:
 for s in q['steps']:
  st=int(s['address'],16);assert at(st,4)==cur[st-base+2048:st-base+2052]
us=Archive(a['PL00_U.ARC']);fx=render(us,88,0,parts(us,0,88)[6:8]);assert np.count_nonzero(fx)==83
effect=[]
for key,p in [('current_PL00',B/'shibuki_audit/prepared_hurt_base01/PL00_U.ARC'),('current_PL02',B/'shibuki_audit/prepared_ultimate_return01/PL02_U.ARC')]:
 ar=Archive(p.read_bytes());v=ar.layer(88)[0];assert np.all(v[fx>0]==6)
 effect.append({'archive':key,'original83_world_positions_present':True,'current_index':6,'original_index':12,'original_whole_tiles':[7,8],'original_part_positions':[[-19,-26],[-3,-26]]})
con={'source_report_sha256':sha(rp.read_bytes()),'passed':True,'native_read_only':True,'native_execution':False,
 'actual_PS1_dispatch':{'address':'0x80037484','reads_shot_type_at_offset':'0x96','jump_table_address':hex(jumpbase),'raw_bytes':at(jumpbase,60).hex(),'targets_by_shot_type':{str(k):hex(v)for k,v in enumerate(targets,2)},'frost_shot_types':[2,11],'cyclone_shot_types':[7,16],'charged_soul_body_shot_type':12},
 'BR20_read_only_binding':{'bin':rel(curp),'exe_sha256':sha(cur),'source_US_exe_sha256':sha(exe),'listed_blocks_byte_exact':blocks,'jump_table_and_selected_animation_steps_exact':True},
 'effect83':effect,
 'conclusions':[
 '원US PL00/PL02는 88=89 x−1에83색인픽셀 효과를 얹은 표시다. 실제조립은몸6파트→효과2파트→마지막몸1파트 순서다. 두16×16타일7/8·파트위치(−19,−26)/(−3,−26)가 동일하고 효과원색인은12다. 현재 시부키 두ARC의 같은83좌표는색인6이다. 원총83모양을보호하되나나의색인12를그대로적용하면안된다.',
 '원US PL00/PL02와현PL00의95→96은5층 및32부분RGBA가x+1 exact다. 현PL02는body0 160px/overlay5 201px차이여서원관계기반신규공통화와현재픽셀동일성은구별한다.',
 '현PL02 88/89의base층은이동후198px차이(그중83은원효과)이며overlay5그림은이동exact다. 88새동기화는원효과83좌표·조립앞뒤를보호하고별도몸차이를무심코효과로복사하지않는다.',
 '88/89와95/96은각각서로만raw를공유하고97은독립이다. 빈부분층의record가다른참조와공유되므로report.frames.layers.record_owners전체를보존한다. PL02빈층6/7/8은표시가0이어도파트좌표는단순이동이아니다.',
 '그림95/96은프로스트타워표95와차지소울보디표96에서사용되고복제체표97은그림96한개다. 그림95와표95·그림97과표97은동일개념이아니다.',
 'PS1실제명령0x80037484와0x80010444점프표가shot_type2/11을frost초기화0x80037db0으로,7/16을cyclone초기화0x80037f78로보낸다. 후자는7이면표104,16이면표105. 둘다첫그림97→81→99/98이며표95/96앞의138139도이전그림연결대상이다.',
 'player_weapon_pose의event0x80에서별도무기객체를생성하므로95/97몸체에실제무기이펙트를그려넣지않는다. 상대step0은land_or_fall로종료하므로표말미96ticks를실제고정대기라고주장하지않는다.',
 '95의낮게펼친양손·떠있는하체와97의가슴앞두팔준비각도를현재수용그림과원표의연결범위로유지한다. 스프라이트손끝좌표로발사점을자동결정한다는근거는없고,정확무기발생월드좌표는이번짧은읽기범위에서추가검증하지않았다.'
 ],'actually_viewed':[{'path':q['path'],'sha256':q['sha256']}for q in j['boards']],
 'visual_observations':['원US 두판에서88효과/89몸체 및95/96한픽셀호흡관계를실제확인했다.','현재PL00의95/96은같은자세이나PL02는하체/의상다름을실제두판에서확인했다. 새원화수용이나실기검사로확대하지않는다.'],
 'limitations':['원본·BR20 명령바이트를읽고디스어셈블했으며MIPS실행/게임조작은하지않음.','새후보패킹/원화제작없음. 전모션미술완료/사용자수용아님.']}
(O/'conclusions.json').write_text(json.dumps(con,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'report_sha256':sha(rp.read_bytes()),'conclusions_sha256':sha((O/'conclusions.json').read_bytes()),'dispatch':con['actual_PS1_dispatch']['targets_by_shot_type']}))
