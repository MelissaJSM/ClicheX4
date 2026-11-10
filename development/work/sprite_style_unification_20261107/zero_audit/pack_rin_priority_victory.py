"""Add the root-reviewed victory5 to the accepted seven-ref Rin body stage."""
from pathlib import Path
import sys,json
D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_priority_body as core
core.P=D/'rin_extension/prepared_priority_body_v1/PL01_U.ARC'
core.SHA='1adc775ad1f81a857daeced21994057d22431b4e9464d395b822acefb096007b'
core.ART=D/'rin_extension/detail_priority_singles/registered_v4'
core.OUT=D/'rin_extension/prepared_priority_victory_v1'
core.EXPECTED_SHA={'b1_005':'4e1941d6fc445b1e6f2dad72bc980915335ca55a87387d199a0d0fd2c984a9b8'}
core.MAP={(1,5):('b1_005',False)}
if __name__=='__main__':
 core.main();p=core.OUT/'proposal.json';j=json.loads(p.read_text('utf8'));j['cumulative_main_refs']=50;j['victory5_included']=True;j['verification'].pop('previous42_exact',None);j['verification']['previous49_exact']=True;j['user_accepted']=False;j['art_review_source']='root reviewed registered_v4 comparison';p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
