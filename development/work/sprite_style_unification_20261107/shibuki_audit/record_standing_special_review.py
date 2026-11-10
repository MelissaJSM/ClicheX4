"""실제 열람한 특수3 정적판과 원순서판을 별도 근거로 기록한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write

def item(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes()),'actually_viewed':True}

def main():
    out=H/'standing_special_visual_review01.json';need(not out.exists(),'Fresh review')
    groups={
        'base_fourth_readback':[H/f'standing_special_pack02/{name}.png' for name in ('base_readback','fourth_readback','partial_095','partial_097')],
        'ultimate_readback':[H/f'ultimate_special_pack01/{name}.png' for name in ('before_readback','after_readback','partial_095','partial_097')],
        'native_neighbors':[H/f'standing_special_connections01/{form}_{group}.png' for form in ('base','fourth') for group in ('frost_soul','cyclone')],
        'actual_table_order':[H/f'standing_special_sequence01/{form}_id{seq}_ordered.png' for form in ('base','fourth','before','after') for seq in (95,104)],
        'ultimate_registration':[H/f'{folder}/{form}_comparison.png' for folder in ('ultimate_special_native01','ultimate_special_common_probe01','ultimate_special_targets01') for form in ('before','after')],
        'ultimate_index_grids':[H/f'ultimate_special_inspection01/{ref:03}_grid.png' for ref in (95,97)]}
    report={'reviewer':'overhaul_ui','candidate_assets':{
        'PL00_U.ARC':'fdba798cc2586f53f576d9255a2b44ddfffda7b7dc850effc7ee4dace5dfc08e',
        'PL02_U.ARC':'26fd4c46813775ae7a2210b463725952abbabc5f3c172eafb7b5533f994168ce'},
        'groups':{key:[item(p) for p in paths] for key,paths in groups.items()},
        'observations':[
            '기본/포스95의 낮게 펼친 손과 교차한 발,97의 가슴앞 양팔에서 새 머릿결·소매·상의 구획이 대기와 이어진다. 포스95의 초기 붉은가슴은 국소 새원화로 검정/보라 접힘으로 교정되어 최종재추출에서도 유지됐다.',
            '기본/포스32부분판에서 머리 장식·몸통·팔·하체 소유를 확인했다. 새 확정 목·팔꿈치·무릎 단절이나 기본소매의 얼굴 침범을 찾지 못했다.',
            'Ultimate새95/97은 구형 큰 단색머리와 검은뒤다리 덩어리가 줄고 선글라스·옷깃·샌들 구분이 살아 있다. 두 의상의 머리/사지/손 공통화 후에도 맨팔과 재킷 소매가 구별된다.',
            'Ultimate후폼의 퍼지는 옷단은 최초 확대원화에서 우려했지만 원설정화를 직접 대조하니 실제 설정 요소다. 이 이유만으로 반려하지 않는다. 대기 몸통과 새옷 주름을 비교했고 새모양을 승인된 설정으로 새로 단정하지 않았다.',
            '97 후폼 팔 뒤의 뒤머리 안쪽 보라1셀은 새후폼 원화에서 before로 공유했다. 양폼 알파관계를 맞추기 위해 삭제하거나 검정으로 채우지 않았다.',
            '원표95의138→139→96→95→96,104의97→81→99→98→99 네폼 정적8판에서 추가 확정 크기급변·팔다리분리는 찾지 못했다. 펼친팔/웅크림 등 동작상 너비변화는 유지된다.'
        ],
        'reference_review':item(ROOT/'character/ver_buki_riko/buki(ultimate armor).webp'),
        'scope_limits':[
            '실제 열람은 정적 재추출·부분·원순서판이다. 연속 동영상이나 게임 실기 관찰로 세지 않는다.',
            '원표5개와604canvas 검사·새참조 원MIPS는 별도 보고에 있으며 무기객체 발생위치/물리/음향/외부상태를 재현한 것이 아니다.',
            '원표 말미 상대step0의96호출을 실제고정대기로 주장하지 않는다.',
            '새95/96/97 밖의85..92·차량/호버·보류135 등 잔여는 미완료이고 전체 사용자 수용도 아니다.'
        ],'new_confirmed_visual_break_found':False,'runtime_verified':False,'user_final_acceptance':False}
    write(out,report);print(json.dumps({'images':sum(map(len,groups.values())),'sha256':sha(out.read_bytes())}))

if __name__=='__main__':main()
