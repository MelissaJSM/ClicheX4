"""원화4파일과 독립재구성5판의 실제열람 범위를 별도 기록한다."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;N=D.parent;W=N.parent;ROOT=W.parents[1];H=W/'shibuki_audit'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
 report=D/'report.json';r=json.loads(report.read_text('utf8'));assert r['passed']and not(D/'visual_review.json').exists();source=[H/d/'generated_v1.png'for d in('hover_ultimate_inputs01','hover221_arm_inputs01','hover221_reach_inputs01','hover_ultimate_inputs02')];sheets=[D/f'readback_{n:03}.png'for n in(221,223,225,227,229)]
 observations=['첫4 원화에서221의반대팔이허리에있던부분을첫국소가높은팔로바꿨고두번째국소가그손을더올린것을실제원화파일에서구분했다. 최종재구성221의오른손은귀와별도로읽히며허리의세번째팔잔류를찾지못했다.','223/225/227 새머리·접힌팔과신발은원래의서로다른자세를유지하는것으로보이며독립재구성판에서새확정목/팔꿈치/발목절단을찾지못했다.','229의두높은손과굽힌무릎/신발이독립재구성으로나타나며,상체0과하체5를합쳤을때확정적인허리틈을찾지못했다. 하체5만의분리표시는의도된계층이다.','밝은테두리/발높이와15jet의실제접점,사격팔5및게임내CLUT변화는이번5판에서수용판정하지않았다. 원화와목표층의exact는최종미술/실기완료와구분한다.']
 v={'actually_viewed':True,'parent_sha256':r['parent_sha256'],'candidate_sha256':r['candidate_sha256'],'report':ref(report),'generated_source_files':[dict(ref(p),actually_viewed=True)for p in source],'generated_source_cell_count':7,'reconstructed_sheets':[dict(ref(p),actually_viewed=True)for p in sheets],'observations':observations,'scope':'생성원화4파일/7셀과재구성5몸체5판직접열람. 실제완성ARC재독출/사격5/원FX/MIPS/실기검사는HUD별도범위.','art_or_ARC_modified':False,'runtime_verified':False};(D/'visual_review.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
 for name,h in r['source_files'].items():assert sha(ROOT/name)==h
 files=[D/'verify_sources.py',Path(__file__).resolve(),report,D/'visual_review.json',*sheets,*[p for p in(D/'reconstructed').iterdir()if p.is_file()],*[ROOT/name for name in r['source_files']]];unique=list(dict.fromkeys(files));(D/'READER_LOCK.json').write_text(json.dumps({'files':[ref(p)for p in unique]},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'report':sha(report),'visual':sha(D/'visual_review.json'),'reader_lock':sha(D/'READER_LOCK.json'),'locked_files':len(unique)}))
if __name__=='__main__':main()
