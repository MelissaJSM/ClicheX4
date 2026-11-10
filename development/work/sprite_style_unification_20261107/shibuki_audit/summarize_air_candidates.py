"""공중 22개 새 몸체 후보의 출처/열람/잔여 작업을 묶는다. ARC 수정 없음."""
from pathlib import Path
import json,sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
from scripts.prepare_shibuki_ultimate_production import records
from src.psx_player import composition_frame
def main():
    parent=H/'prepared_arrival_victory01/PL00_U.ARC';a=Archive(parent.read_bytes());pages=[];allrows=[]
    for i in range(1,5):
        d=H/f'air_detail_inputs{i:02}';o=H/f'air_detail_native{i:02}'
        r=json.loads((o/'registration.json').read_text('utf8'));need(r['source_sha256']==sha((d/'generated.png').read_bytes()),'Generated art changed')
        views=[{'path':(o/f'{form}_comparison.png').relative_to(ROOT).as_posix(),'sha256':sha((o/f'{form}_comparison.png').read_bytes())}for form in('base','fourth')]
        for row in r['rows']:
            need(row['original_foot_y']==row['new_foot_y'],'Foot bottom moved')
            need(sha((ROOT/row['native_png']).read_bytes())==row['sha256'],'Native input changed')
        allrows+=r['rows'];pages.append({'page':i,'generated':(d/'generated.png').relative_to(ROOT).as_posix(),'source_sha256':r['source_sha256'],
                                      'registration':(o/'registration.json').relative_to(ROOT).as_posix(),'registration_sha256':sha((o/'registration.json').read_bytes()),
                                      'source_size':r['source_size'],'scale':r['source_scale'],'actual_viewed_comparisons':views})
        mf=d/'manifest.json'
        if mf.exists():
            m=json.loads(mf.read_text('utf8'));m.update(generation_started=True,generation_completed=True,generated_sha256=r['source_sha256'],
                                                     generated_dimensions=r['source_size'],native_registration_complete=True,game_written=False,
                                                     prompt_file_is_prepared_brief_not_claimed_exact_tool_text=True);write(mf,m)
    heads=[]
    for n in range(33,55):
        c=composition_frame(a.c,5,n)
        heads.append({'ref':n,'record_hex':records(a.c,5,n).hex(),'native_parts':c['parts']})
    write(H/'air_detail_source_index01.json',{'candidate_only':True,'source_parent_sha256':sha(parent.read_bytes()),'new_body_candidates':22,
          'all_22_foot_bottom_y_exact':True,'original_canvas_origin':[160,160],'palette_bytes_changed':False,'global_figure_resize':False,
          'old_head_body_overwrite':False,'pages':pages,'targets':allrows,'head_composition_source':heads,
          'pending':['基本/포스 공통 머리·손과 의상 파츠 경계 정합','사격34..54짝 새 팔/원총구 정합','부분 아머16마스크×2팔 회귀','원타일/압축/조립 용량 및 GPU 검증'],
          'not_covered_air_dash_refs':[93,94],'resource_written':False,'runtime_verified':False,'full_style_completion':False})
    path=H/'FULLFORM_LEDGER.md';text=path.read_text('utf8');text=text.replace('새 공중 원화는 아직 생성 전이다.','새 공중 몸체33..53 홀수11자세×기본/포스의22개 후보는4페이지 생성·고정 셀배율 등록 및8비교 실제 열람을 마쳤다. 발바닥 Y22개가 원형과 같으며 사격짝/부분 파츠 정합과 패킹은 진행 전이다. `air_detail_source_index01.json`을 따른다. 아직 동결192표시 집계에는 포함하지 않는다.');path.write_text(text,'utf8')
    print(json.dumps({'pages':4,'candidates':len(allrows),'actual_viewed_sheets':8,'heads':heads[:4]}))
if __name__=='__main__':main()
