"""실제 열람한 46장 C04 검토 기록을 해시가 있는 목록으로 보존한다."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/'work/overhaul_20261105/sprites'
OUT=ROOT/'work/overhaul_20261105/ui/c04_visual_review/review_inventory.json'
NOTES={
 'zero_base':'수용 대기 대비 동일 정체성. 굽힌 다리/회전/색반전 피격을 별도 크기 결함으로 단정하지 않음.',
 'zero_special':'Riko 체이서와 RideArmor 머리 누락 별도 수정. 42..49는 원본부터 부분 VRAM 업로드이며 정상 탑승 호출에서 선택되지 않는 참조.',
 'x_base':'모든 페이지 실제 열람. 213..220은 몸통 파츠가 없는 기본형에서는 진입 조건이 충족되지 않음. 아머 상태는 별도 판단.',
 'x_fourth':'Nana1..32 붉은 종아리 수정. Nana213..220은 포스에서도 사용되는 노바이며 본체6개 교정, 순수 에너지218/219 보존.',
 'x_preultimate':'기준 BIN에서는 일반 의상 복사. 별도 C03 최종 패치와 독립검사 완료. 133..139는 등장 event140 이전 공통 몸체라 캡슐 전 의상으로 교정.',
 'x_ultimate':'Shibuki1/2 대기-사격 의상 디테일 교정. 정적 full-overlay sheet와 실제 등장 event별 파츠 표시를 구분해야 함.',
}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    pages=[];projects={}
    for project in ('ver_buki_riko','ver_rin_nana'):
        audit=json.loads((DIR/project/'audit.json').read_text('utf8'))
        frames=json.loads((DIR/project/'frames.json').read_text('utf8'))
        projects[project]={'baseline':audit['source_bin'],'baseline_sha256':audit['source_sha256'],
            'rendered_references':audit['rendered_references'],'unrendered_references':audit['unrendered_references']}
        for group,count in [('zero_base',4),('zero_special',3),('x_base',4),('x_fourth',4),('x_preultimate',4),('x_ultimate',4)]:
            ids=sorted(int(k.rsplit('_',1)[1])for k in frames if k.startswith(group+'_'))
            for page in range(count):
                p=DIR/project/f'{group}_{page:02}.png'
                assert p.is_file()
                pages.append({'project':project,'group':group,'page':page,
                    'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),
                    'frames':ids[page*64:(page+1)*64],
                    'actual_image_viewed':True,'method':'view_image original-detail; native 2x nearest sheet, fixed world origin160,160',
                    'notes':NOTES[group]})
    assert len(pages)==46
    issues=[
      {'id':'C04-Shibuki-Ultimate-idle-shot','project':'ver_buki_riko','refs':[1,2],
       'group':'x_ultimate','finding':'대기0/115 계열과 다른 머리장식·상의 디테일',
       'artifact':'work/overhaul_20261105/ui/c04_shibuki_ultimate/candidate.json',
       'proposal':'work/overhaul_20261105/sprites/c03_final_v1/ver_buki_riko/proposal.json',
       'status':'C03 최종 PL02와 함께 패킹 완료, 독립 full RGBA가 indexed 후보1/2와 완전 일치'},
      {'id':'C04-Nana-Fourth-calves','project':'ver_rin_nana','refs':list(range(1,33)),
       'group':'x_fourth','finding':'짧은 구두 붉은색이 종아리까지 확장됨',
       'proposal':'work/overhaul_20261105/ui/nana_legs_v1/proposal.json','status':'수정·정적 검증 완료, 루트 통합'},
      {'id':'C04-Riko-Chaser','project':'ver_buki_riko','refs':list(range(14,42)),
       'group':'zero_special','finding':'원작 Zero 체이서 몸체 28참조 잔존; 색상 잔상 문제가 아님',
       'proposal':'work/overhaul_20261105/ui/riko_chaser_v1/proposal.json','status':'수정·재현·RideArmor 병합 검증 완료, 루트 candidate03 통합'},
      {'id':'R03-Riko-RideArmor-head','project':'ver_buki_riko','refs':[n for n in range(66,86)if n!=80],
       'group':'zero_special','finding':'원작 Zero 탑승 머리 19참조 잔존',
       'proposal':'work/overhaul_20261105/sprites/patch_v1/ver_buki_riko/proposal.json','status':'sprites 담당 교정, Chaser와 byte 충돌0 검증'},
      {'id':'C04-Nana-Fourth-Nova','project':'ver_rin_nana','refs':list(range(213,221)),
       'group':'x_fourth','finding':'8참조 기본층이 원본과 완전 동일; 이 중 6개에 X 몸체 잔존, 218/219는 순수 효과. 실제 몸통 파츠에서도 도달',
       'evidence':'work/overhaul_20261105/ui/nana_fourth_nova/reference.json',
       'proposal':'work/overhaul_20261105/ui/nana_fourth_nova_v1/proposal.json',
       'status':'본체6참조 수정·독립 재현·legs byte 충돌0·UV 경계·6종 거부 검사 완료. candidate04 실제 포스에서8참조 전부 RAM/GPU 업로드 일치'},
    ]
    result={'reviewer':'overhaul_ui','inspection_scope':'두 기준 BIN의 추출 시트 46장 실제 이미지 열람. 게임 장면 전수 재생을 의미하지 않음.',
      'projects':projects,'sheet_pages':pages,'reviewed_page_count':len(pages),'issues':issues,
      'usage_classification':[
        {'refs':list(range(42,50)),'groups':['zero_special'],'classification':'원본 1타일 부분 업로드, 정상 Ride Chaser setter 경로 미선택',
         'evidence':'work/overhaul_20261105/ui/riko_chaser/audit.json','limitation':'프로그램 전체의 절대 미도달 증명 아님. 임의 VRAM 이력을 만들어 복원하지 않음.'},
        {'refs':list(range(133,140)),'groups':['x_fourth','x_ultimate','x_preultimate'],
         'classification':'등장 event140 이전 공통 본체. full-overlay sheet만 보고 재킷 누락으로 판단하면 안 됨.',
         'evidence':'work/overhaul_20261105/ui/c04_visual_review/frame_usage.json','followup':'PL02 C03 캡슐 전 의상 대상에 포함해 sprites 담당 전달'},
        {'refs':list(range(213,221)),'groups':['x_base','x_preultimate'],
         'classification':'몸통 파츠 bit2 없는 상태에서는 진입 불가. 기본 무아머 표시의 원작 잔존만으로 결함 단정 불가.'},
        {'refs':list(range(213,221)),'groups':['x_fourth','x_ultimate'],
         'classification':'몸통 파츠와 충전 에너지 조건에서 사용. Ultimate 전용이 아님.',
         'evidence':'work/overhaul_20261105/ui/c04_visual_review/frame_usage.json'},
      ],
      'additional_root_image_review':['ver_rin_nana zero_base00..03','ver_rin_nana zero_special00..02',
        'ver_rin_nana x_base00..03','ver_rin_nana x_fourth00..03','ver_rin_nana x_ultimate00..03'],
      'unverified':['노바의 실제 framebuffer 정밀 비교와 모든 방향/배경의 전수 재생','C03 생성 결과 전체의 최종 병합 후 전환 재생',
        '정상 반전·애니메이션 타이밍·배경 위 시인성의 전수 실기','16 부분 VRAM 참조의 전체 프로그램 접근성',
        '시트 창 바깥 큰 이펙트 전체를 모든 개별 PNG에서 별도 전수 열람하지는 않음'],
      'not_defects_by_itself':['다리 굽힘/웅크림 때문에 낮아진 바운딩박스','베일/귀가 차지하는 외곽 크기 차이',
        '정적 팔레트로 그린 피격·효과 반전색','전체 아머 레이어를 동시에 겹친 출현 전반부 미리보기'],
      'checkpoint_search':{'evidence':'work/overhaul_20261105/ui/riko_chaser/checkpoint_scan.json',
        'result':'514파일/238고유 상태에서 실제 stage5 또는 ride animation65..76 상태 없음. stage7 animation60은 Hawk RideArmor로 재분류.',
        'mutations':False,'clone_created':False},
      'runtime_addendum':{'evidence':'work/overhaul_20261105/ui/riko_chaser_v1/runtime_fresh_frame14.json',
         'scope':'루트가 새 부팅한 candidate03의 실제 Riko stage5 animation65/frame14. 디스크/RAM/VRAM/CLUT 일치 및 몸/손/좌석 화면 실제 열람.',
         'not_verified':'다른 체이서27참조 전체 재생 및 오르막/내리막'},
      'nova_runtime_addendum':{'evidence':'work/overhaul_20261105/ui/nana_fourth_nova_runtime01/evidence.json',
         'scope':'candidate04 실제 Nana full Fourth parts15 Ultimate0에서 213..220 전부 관측. 각 디코드/RAM/GPU bytes 일치, 비원자 관측20안정표본 불일치0.',
         'palette_correction':'work/overhaul_20261105/ui/nana_fourth_nova_runtime01/palette_correction.json',
         'not_verified':'초기 부가 합성기의 잘못된CLUT 가정으로 만든 이미지는 무효. 수정된 별도F1 palette 재합성을 동시 framebuffer로 표현하지 않음.'},
      'C03_independent_final':['work/overhaul_20261105/ui/c03_independent/ver_rin_nana/verification.json','work/overhaul_20261105/ui/c03_independent/ver_buki_riko/verification.json'],
      'runtime_verified':False}
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'output':str(OUT),'pages':len(pages),'projects':projects},ensure_ascii=False))
if __name__=='__main__':main()
