"""사격01의 기술일치와 확인된3셀 소유문제를 구분해 증거를 잠근다."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;S=W/'root_shibuki_hover';O=D/'shibuki_base_hover_shots01';A=W/'nana_audit/shibuki_base_hover_shot_art_read01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(R).as_posix();read=lambda p:json.loads(p.read_text('utf8'))
def write(name,obj):
 with(O/name).open('x',encoding='utf8')as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
r=read(O/'report.json');assert sha(O/'report.json')=='0b98a7d07250b13ea7359c075ad8ea68e05bb50273d82e4d8f6b57886edc2961'
files=read(O/'INPUT_LOCK.json')['files'].copy()
def track(p):files[rel(p)]=sha(p);return{'path':rel(p),'sha256':sha(p)}
for p,h in files.items():assert sha(R/p)==h,p
viewed=[track(S/f'shot_composed01/comparison_{n}.png')for n in(222,224,226,228,230)]
for p in r['sheets']:assert sha(R/p['path'])==p['sha256'];viewed.append(track(R/p['path']))
viewed.append(track(O/'semantic_common_cells.png'));assert len(viewed)==11
assert sha(A/'visual_review.json')=='52b4fb63a775947119e094900f5748c594aead53384b91f829a5f6ec2bc00e6e'
peer={k:track(A/k)for k in('visual_review.json','READER_LOCK.json')}
semantic=read(O/'semantic_common_cells.json');assert sha(O/'semantic_common_cells.json')=='443a446f001fcbc3ca68b6f3dee35b559f3cf2f79ae9ba8ffa054da070f45460'
write('visual_review.json',{'actually_viewed':True,'observer':'/root/hud_checkpoint','boards':viewed,'board_count':11,'observations':['제작자합성5판과독립합성5판,3셀좌표확대1판을실제열람했다.','222/224의길게뻗은소매는손목과총뒷부분으로이어지고확정된틈은찾지못했다.222/230의반대높은팔은1개만남아발사쪽옛주먹이추가팔처럼남지는않는다.','226/228의접힌팔은손목·커프·소매로이어진다.228짧은정본총은한개이며원화의긴총이겹쳐남거나떠보이는문제는못찾았다.','독립mask11 및arm2판에서도팔/목/하체의큰절단은못찾았다.하지만연결성분1과해시일치가의상소유의정확성을대신하지는않는다.','추가확대에서224손목(-18,-6)의빨간기본색1셀과230가슴앞(-6,-2)흰색/(-7,-1)빨강2셀이포스9피부대신공통으로남는위치를확인했다.후속02소유정정대상으로Root에전달했다.'],'source_peer':peer,'limits':['총에인접한불투명픽셀수에는얼굴·머리도포함될수있으므로특히228의접촉숫자를전부손목피부라고세지않았다.','원화10셀은직접재양자화했지만이번HUD시각열람은등록전원화3파일전수열람을포함하지않는다.동료는별도등록4판을보았다.','최종ARC/원MIPS/실기/탄환움직임은미실행.'],'source_or_resource_modified':False})
write('conclusions.json',{'technical_reconstruction_passed':True,'art_ownership_acceptance':'01의3셀은후속02소유정정대상.01을최종미술통과나동결후보로확대하지않는다.','scope':'PL00호버사격5 국소팔등록진단','report':track(O/'report.json'),'visual':track(O/'visual_review.json'),'semantic_cells':track(O/'semantic_common_cells.json'),'input_lock':track(O/'INPUT_LOCK.json'),'counts':r['counts'],'checks':['생성10셀을각고정96/팔레트0·16으로직접재양자화하고등록PNGexact확인.제작함수미호출.','body04의25층은이전독립검사03과바이트/색인동일이며설명인코딩만정정됐다.','5팔편집창/원화총제외창/의상arm7/정본총→25목표층을독립재계산하여exact.','80부분(mask8..15×arm1/2)은각1연결성분이고얼굴guard밖·공통하체·총71guard RGBAexact.','원총구5좌표와수용34의60불투명+11투명정본이일치한다.정본60은CLUT16에서다른색이되므로공통0및overlay제외가필수다.','228얼굴창7셀은정본guard의앞그리기로변경되며그밖얼굴은exact.이를얼굴전체불변으로기록하지않는다.','총/팔의변경은하체8에미치지않아기존body04의원15jet접점관계가유지된다.새효과원코드실행은없다.'],'confirmed_ownership_issue':semantic['rows'],'root_followup_decision':'협업메시지에서Root는shared_skin을arm & base12/13으로한정하고3셀의실제Fourth9를arm7에두는shot_composed02를별도작성하겠다고알렸다.이번기록은02를검사하지않았다.','reader_correction':r['reader_assumption_correction'],'producer_functions_imported_or_called':False,'inputs_modified':False,'new_art_generated':False,'ARC_created':False,'new_MIPS_execution':False,'runtime_verified':False})
for p in(Path(__file__),D/'read_shibuki_base_hover_shots01.py',D/'read_shibuki_base_hover_shot_semantics01.py',O/'conclusions.json'):track(p)
for p,h in files.items():assert sha(R/p)==h,p
write('READER_LOCK.json',{'files':dict(sorted(files.items())),'original_inputs_unchanged':True,'source_or_resource_writes':False})
print(json.dumps({k:sha(O/k)for k in('report.json','visual_review.json','conclusions.json','READER_LOCK.json')}))
