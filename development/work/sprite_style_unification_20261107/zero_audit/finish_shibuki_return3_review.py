from pathlib import Path
import hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).parent;ROOT=D.parents[2];H=D.parent/'shibuki_audit';O=D/'shibuki_ultimate_return3_independent01';sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
# 기술결과의 영역 표기만 정확히 한다. 검사 내용과 입력은 불변이다.
for script in('prepare_shibuki_return_reader.py','verify_shibuki_ultimate_return3_independent.py'):
 p=D/script;t=p.read_text('utf8');t=t.replace("'local_arm_rectangle':[-4,5,-3,5]", "'local_arm_region':{'world_x':'x<=-4 or x>=5','world_y_inclusive':[-3,5]}");p.write_text(t,'utf8')
rp=O/'report.json';r=json.loads(rp.read_text('utf8'));q=r['source_pose_registration'];q.pop('local_arm_rectangle',None);q['local_arm_region']={'world_x':'x<=-4 or x>=5','world_y_inclusive':[-3,5]};rp.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
sources={'accepted_PL00':H/'prepared_hurt_base01/PL00_U.ARC','parent_PL02':H/'prepared_ultimate_victory01/PL02_U.ARC','candidate_PL02':H/'prepared_ultimate_return01/PL02_U.ARC'}
ar={k:Archive(p.read_bytes())for k,p in sources.items()};Y,X=np.indices((384,384));Y-=160;X-=160
def bbox(m):
 y,x=np.nonzero(m);return [int(x.min()-160),int(y.min()-160),int(x.max()-159),int(y.max()-159)]if len(x)else None
rows=[];pics=[]
for key,a in ar.items():
 for form,mask in(('before',15),('after',0)):
  z=a.layer(156)[0].copy()
  if mask:
   for pb in(8,5,7,6):v=a.layer(156,pb)[0];z[v>0]=v[v>0]
  groups={}
  for name,m in(('left_hand',(X<=-9)&(Y>=-7)&(Y<=7)&np.isin(z,(10,11,12,13))),('right_hand',(X>=9)&(Y>=-7)&(Y<=7)&np.isin(z,(10,11,12,13))),('left_foot',(X>=-10)&(X<0)&(Y>=12)&(Y<=25)&(z>0)),('right_foot',(X>=0)&(X<=10)&(Y>=12)&(Y<=25)&(z>0))):
   groups[name]={'bbox_world_exclusive':bbox(m),'opaque':int(m.sum()),'indexed_cells':[[int(x-160),int(y-160),int(z[y,x])]for y,x in np.argwhere(m)]}
  display_form=('fourth'if mask else'base')if key=='accepted_PL00'else form
  rows.append({'source':key,'form':display_form,'origin':[0,0],'body_bbox':bbox(z>0),'semantic_roi_only':groups});pics.append((key+' '+display_form,a.composite(156,mask)[0]))
boxes=[im.getbbox()for _,im in pics];box=(min(q[0]for q in boxes)-3,min(q[1]for q in boxes)-3,max(q[2]for q in boxes)+3,max(q[3]for q in boxes)+3)
cw=(box[2]-box[0])*5+12;ch=(box[3]-box[1])*5+26
board=Image.new('RGB',(3*cw,2*ch),'#263345');dr=ImageDraw.Draw(board)
for i,(name,im)in enumerate(pics):
 x=(i//2)*cw;y=(i%2)*ch;dr.text((x+3,y+4),name,fill='white');p=im.crop(box).resize(((box[2]-box[0])*5,(box[3]-box[1])*5),Image.Resampling.NEAREST);board.paste(p,(x+4,y+22),p)
bp=O/'contact_comparison.png';board.save(bp)
files=[]
for name,lines in(('player.c',[[160,180],[1142,1155]]),('player_enter.c',[[638,659]])):
 p=ROOT/'work/research/decomp/src/main'/name;code=p.read_text('utf8').splitlines();files.append({'path':rel(p),'sha256':sha(p),'ranges':lines,'excerpts':['\n'.join(code[lo-1:hi])for lo,hi in lines]})
contacts={'scope':'귀환156 원점·손발 비교 및 코드 읽기에 근거한 물리제약 구분','sources':{k:{'path':rel(p),'sha256':sha(p)}for k,p in sources.items()},'measurements':rows,'code_read':files,'original_sequence_evidence':{'path':rel(D/'shibuki_ultimate_return_relations01/report.json'),'sha256':sha(D/'shibuki_ultimate_return_relations01/report.json')},'inference':['읽은 player_beam_out 첫 단계는 animate_object만 호출하고 종료 표식에서 animation4로 바꾼다. move_object는 다음 단계에서만 실행된다.','player_enter_beam_out는 x속도0/y속도8·air_state1 등을 설정한다. 읽은 해당 경로에는 손끝을 사다리/무기 접점에 결속하거나 스프라이트 불투명 외곽으로 충돌점을 계산하는 코드가 없다.','따라서156의 손끝을 PL00와 숫자상 같게 강제할 직접 물리 제약은 이 경로에서 확인되지 않았다. 같은 원점에서 자세·관절·발 높이를 미술로 검토하는 사안이다. 전체게임의 모든 외부연출 호출을 추적했다는 뜻은 아니다.'], 'actual_runtime_or_MIPS_executed':False,'fresh_board':{'path':rel(bp),'sha256':sha(bp),'view_pending':True}}
(O/'contact_constraints.json').write_text(json.dumps(contacts,ensure_ascii=False,indent=2)+'\n','utf8')
review={'scope':'최종 귀환3 독립 정적 열람','candidate_sha256':r['candidate_sha256'],'technical_report_sha256':sha(rp),'actually_viewed':[{'file':n,'sha256':sha(O/n)}for n in('readback_156.png','readback_157.png','readback_158.png')],'observations':['새156의 머리·의상·신발 명암이 선명해졌고, 발 높이 차이와 팔꿈치·손 연결을 이 판에서 확인했다.','157 새몸테두리는 머리·땋은머리·손을 둘러싸며 옛머리의 가림형상을 새 그림에 덮지 않았다.','158 기존광선·고리 앞에 새몸이 이어진다. 새몸 바깥의 역사효과1875픽셀 원형 및 가려진19저장타일 전체보존은 기술보고에서 따로 확인했다.','세 판에서 추가 확정할 새 관절단절이나 고립 조각은 찾지 못했다. 원손끝과 같은 좌표일 것을 미술 수용조건으로 주장하지 않는다.'],'runtime_verified':False,'user_accepted':False,'whole_project_complete':False}
(O/'visual_review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'report':sha(rp),'visual':sha(O/'visual_review.json'),'contacts':sha(O/'contact_constraints.json')}))
