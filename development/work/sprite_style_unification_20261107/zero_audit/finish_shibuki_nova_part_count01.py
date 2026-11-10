"""파트31/전체38의 원포맷 읽기 결론. 기존 읽기 자료 불변."""
from pathlib import Path
import hashlib,json,struct,sys
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;O=D/'shibuki_nova_part_count_read01';sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from src.psx_player import composition_frame
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def save(name,obj):
 p=O/name;assert not p.exists();p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n','utf8');return {'path':rel(p),'sha256':sha(p)}
r=json.loads((O/'read_data.json').read_text('utf8'));assert sha(O/'read_data.json')=='fc575162bc164f434bb6aa29df32ee866f3b1a6b8994d0b1c9ed7cd65bf53ea2'
orig=Archive(read_disc(ROOT/'MegaMan X4.bin',('PL00_U.ARC',))[0]['PL00_U.ARC']);ps=composition_frame(orig.c,0,220)['parts'];prefix=b''.join(orig.c[p['record_offset']:p['record_offset']+4]for p in ps)
fixed=W/'shibuki_audit/nova_strike_base_targets01/effect220_prefix.bin';assert prefix==fixed.read_bytes()and len(prefix)==24*4
support=Path(sys.argv[1]).resolve();q=json.loads(support.read_text('utf8'))
findings=[
 {'finding':'24는 현재 native_pose_pack 제작기의 보수적 가드이며 원US per-composition상한이 아님','evidence':['native_pose_pack.py66/73/125','원US PL00219가28base파트','repack_parts는headercount를16bit로저장하며24검사없음']},
 {'finding':'원US/BR27 본체렌더러는16bit파트개수를읽고모든record를순회','evidence':['0x800243fc 상위16offset;0x80024400 lhu count','0x80024858 record+4;0x80024868 count-1;0x8002486c 재반복','파트당0x28 primitive와8byte drawmode 전진.24개고정스택배열없음']},
 {'finding':'본체렌더러의1000은프레임공용카운터상한','evidence':['0x80024368/0x8002445c slti0x3e8;0x80024468 increment','아머함수0x8002588c는count16bit/감소루프이나이카운터검사·증가없음','공용버퍼1024개와remaining24는로컬per-layer24가드의근거로동일시할수없음']},
 {'finding':'새220의31base/7armor=38은포맷상처리가능한범위이며제작기24가드만으로거부할이유없음','evidence':['원US/현재220은24base+11armor=35','새31base는원효과24records에새7record추가인별도제작정책','후보31/38 실제MIPS/공용패킷포인터실행은이읽기에서미실행']},
 {'finding':'32tile/4096decodedbyte제약과조립파트개수는별도','evidence':['같은타일여러파트재사용가능','고정조립은행용량/다른record공유/타일U0·V끝/GPU경계는계속독립검사필요']},
]
result={'scope':'Shibuki PL00 Nova220의31base+7armor 파트 정책에 대한 읽기 결론. EXE/ARC/원화 변경 없음.','input_read_data':{'path':rel(O/'read_data.json'),'sha256':sha(O/'read_data.json')},'independent_queue_read':{'path':rel(support),'sha256':sha(support)},'original_effect220_prefix_exact':{'records':24,'bytes':96,'sha256':hashlib.sha256(prefix).hexdigest()},'findings':findings,'candidate_counts_are_producer_proposal_not_executed':{'base':31,'head':1,'body':3,'arm':1,'leg':2,'mask15_total':38,'primitive_bytes':1520,'drawmode_bytes':304,'mask0_primitive_bytes':1240,'mask0_drawmode_bytes':248,'original_mask15_total':35,'total_extra_vs_original_mask15':3},'remaining_acceptance':['고정후보에서원디렉터리→obj+3c→실제기본/아머렌더러가31+7records를양방향모두처리하고packetcursor가38*40/38*8 증가하는지확인','기본mask0/포스15 및부분조합에서원24효과파트의뒤에새몸7이정확히그려지고비대상/전체타일이보존되는지확인','전체프레임공용사용량과1000도달시중단은별도.이번정적검토를혼잡장면/실기/모든전역buffer상태안전증명으로확대하지않음'],'new_native_execution':False,'runtime_verified':False,'candidate_written_or_modified':False}
result['necessary_global_bounds']=q['requested_candidate_arithmetic']['necessary_bounds']
result['counter_exhaustion_not_safe_clipping']=q['base_renderer']['early_exit']
c=save('conclusions.json',result);inputs=dict(r['inputs'])
for p in [Path(__file__),D/'read_shibuki_nova_part_count01.py',O/'read_data.json',O/'conclusions.json',support]:inputs[rel(p)]=sha(p)
for row in r['code_ranges']:inputs[row['disassembly_path']]=row['disassembly_sha256']
for p,h in inputs.items():assert sha(ROOT/p)==h,p
l=save('READER_LOCK.json',{'inputs':inputs,'count':len(inputs),'only_new_evidence_written':True});print(json.dumps({'conclusions':c,'lock':l}))
