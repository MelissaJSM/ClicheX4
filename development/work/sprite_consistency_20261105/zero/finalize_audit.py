"""실제 열람한 제로 계열 비교 시트와 검증 결과를 정리한다. 게임 입력은 변경하지 않는다."""
from pathlib import Path
import json
import sys
import struct
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.export_zero_consistency import write
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba

WORK=ROOT/'work/sprite_consistency_20261105/zero'
OUT=ROOT/'out/sprite_consistency_20261105'
FIX=WORK/'riko/wall_fix'


def main():
    metrics_path=WORK/'riko/head_color_metrics.json'
    metrics=json.loads(metrics_path.read_text(encoding='utf-8'))
    for f in metrics['frames']:
        if f['frame']!=147:
            continue
        a=np.array(Image.open(OUT/'riko/indices/b0_147.png'))
        mask=np.isin(a,[4,8,14]);mask[155:]=False
        y,x=np.where(mask)
        f.update(bbox_world=[int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)],
                 width=int(x.max()-x.min()+1),height=int(y.max()-y.min()+1),colored_hair_pixels=int(mask.sum()),
                 head_roi_world={'y_less_than':-5},excluded_non_head_same_color_pixels=1)
    metrics['method']='실제 머리 영역의 머리색 인덱스4/8/14만 측정. 대기147은 y<-5로 제한해 몸의 같은 색1픽셀을 제외. 윤곽·피부·흰 하이라이트를 포함하는 해부학적 머리크기 자동측정은 아님.'
    write(metrics_path,metrics)

    # Palette-only rendering of already prepared pixels, no art mutations.
    old=(WORK/'riko/PL01_U.ARC').read_bytes();new=(FIX/'prepared_v1/PL01_U.ARC').read_bytes()
    board=Image.new('RGB',(3*256,4*296),'#263442');draw=ImageDraw.Draw(board)
    for row,(bank,num,variant,palrow) in enumerate([(0,39,'normal',0),(1,59,'normal',0),(0,39,'black',13),(1,59,'black',13)]):
        pal=struct.unpack_from('<16H',entry(old,9),palrow*32)
        for col,(label,arc,b,n) in enumerate([('idle147',old,0,147),('before',old,bank,num),('proposed',new,bank,num)]):
            pixels,_=render(arc,b,0 if b==0 else 5,n)
            # Full compared poses, same origin and 4x nearest, including feet.
            im=rgba(pixels,pal).crop((128,124,192,192)).resize((256,272),Image.Resampling.NEAREST)
            board.paste(im,(col*256,row*296+24),im)
            draw.text((col*256+3,row*296+3),f'{variant} b{bank}/{num} {label}',fill='white')
    board.save(FIX/'prepared_v1/normal_black_review.png')

    reports={}
    for ch in ('riko','rin'):
        base=OUT/ch;manifest=json.loads((base/'manifest.json').read_text(encoding='utf-8'))
        body_sheets=json.loads((WORK/ch/'body_review/sheets.json').read_text(encoding='utf-8'))
        findings=[]
        if ch=='riko':
            findings.append({'id':'riko_wall_head_height','status':'confirmed_prepared_root_visual_accepted',
                'frames':['b0_%03d'%i for i in range(38,44)]+['b1_%03d'%i for i in (50,51,53,54,56,57,59,61,63,65)],
                'observation':'벽35~37/대기147에 비해 벽38~43 및 공유 벽 공격 머리의 세로 볼륨이 명백하게 납작함.',
                'evidence':'같은 머리색 인덱스만 비교: 대기147·벽35~37은22×18/188픽셀, 벽38~43은22×14/143픽셀. 폭은 같고 높이만4픽셀 작아 단순 측면 원근으로 설명하기 어려움.',
                'measurement':'work/sprite_consistency_20261105/zero/riko/head_color_metrics.json',
                'before_sheet':'work/sprite_consistency_20261105/zero/riko/wall_head_review.png',
                'prepared_proposal':'work/sprite_consistency_20261105/zero/riko/wall_fix/prepared_v1/proposal.json',
                'prepared_arc_sha256':'36e231a882be87d71d603667a26909025003b88908f939f115d328b0dd4d53dc',
                'verification':'work/sprite_consistency_20261105/zero/riko/wall_fix/verification.json',
                'result':'새머리23×20을 기존목 기준(0,-3)으로 바인딩. 원래 손·팔·어깨는 앞에 보존. 대상16프레임 이외428참조 보존. 검증된 머리만 바뀌고 파츠/좌표/팔레트/타이밍/능력은 유지.',
                'root_review':'root가 prepared_v1 전체 비교를 직접 보고 채택함. 사용자 실기 수용은 아직 없음.',
                'game_applied':False,'runtime_verified':False})
        observations=[]
        if ch=='riko':
            observations=[
                {'frames':['b0_%03d'%i for i in range(111,128,2)],'status':'optional_style_review_not_confirmed_defect',
                 'observation':'지상 베기 후반의 넓은 흰 부츠 면은 대기보다 평평한 인상이 있음. 뻗은 다리와 강한 하이라이트의 포즈 표현일 수 있어 크기 오류나 필수 재제작으로 확정하지 않음. 현재 보존.'},
                {'frames':['b1_%03d'%i for i in range(1,7)],'status':'pose_difference_not_confirmed_defect',
                 'observation':'승리 측면 자세의 얇은 하체는 정면 대기보다 좁지만 다리 원근과 포즈가 달라 전신 bbox 비율로 확대하지 않음.'}]
        else:
            observations=[{'status':'no_confirmed_art_change','observation':'대기·이동·대시·점프·벽·사다리·일반공격·특수기·피격·저체력·등장·승리·귀환·탑승의 몸체315참조 비교에서 새로 반드시 수정해야 할 명확한 불일치는 찾지 못함. 비슷하게 보이도록 억지 확대/축소하지 않음.'}]
        report={'character':ch,'source':manifest['source'],'scope':'최신 BIN의 Zero 플레이어2뱅크 및 낙봉파 내장 몸체. UI/초상화/탄환·별도 오브젝트 효과 전수 실기 감사는 별도.',
          'manifest':(base/'manifest.json').relative_to(ROOT).as_posix(),'canvas':manifest['canvas'],
          'coverage':manifest['coverage'],'counts':{'manifest_entries':len(manifest['frames']),
            'native_png_per_palette':438,'normal_black_palettes':2,'labeled_sheets':len(manifest['sheets']),
            'body_comparison_sheets':len(body_sheets),'body_comparison_refs':sum(len(s['frames']) for s in body_sheets),
            'exact_exe_animation_table_entries':len(manifest['animations'])},
          'review':{'method':'실제 view_image로 대기147와 동작을 같은 원점·배율로 나란히 확인. 몸체26시트315참조와 등장/귀환 빛, Black 대기/벽 대표 비교 열람. 큰 효과는 별도 온전한 뷰포트로 내보냄.',
            'normal_body_sheets_reviewed':[(WORK/ch/'body_review'/s['path']).relative_to(ROOT).as_posix() for s in body_sheets],
            'additional_sheets_reviewed':[(base/x).relative_to(ROOT).as_posix() for x in ('normal/sheets/arrival_light_00.png','normal/sheets/return_light_00.png','black/sheets/wall_00.png')],
            'black_full_visual_audit':False,'black_bitmap_shared_with_normal':True,'runtime_verified_this_audit':False},
          'sheets':[{**s,'path':(base/s['path']).relative_to(ROOT).as_posix()} for s in manifest['sheets']],
          'confirmed_findings':findings,'other_observations':observations,
          'limitations':[
            'bank1 frames42~49는 1타일 부분 VRAM 갱신. raw128바이트는 보존/검증했으나 이전 VRAM 없이 완전 프레임을 복원할 수 없음. 누락 도트 결함으로 판정하지 않음.',
            'bank1 frame80은 실제 빈 프레임이며 누락으로 판정하지 않음.',
            '일반 row0/Black row13은 현재 ARC 그대로. 비zero CLUT 피격색은 역사적 실제 VRAM 스냅샷의 미리보기이며 현 세션 실제 색 검증은 아님.',
            '효과 전용 참조의 팔레트는 몸체 팔레트로 미리보기. 실제 별도 효과 오브젝트 CLUT/색/표시시점을 이 PNG만으로 판정할 수 없음.',
            '낙봉파 static6 23/24는 원래 별도 CLUT0x7803 캡처색을 사용한 내장 몸체. Black에 종속된 새 별도 비트맵은 아님.',
            'EXE의 raw duration/event/relative_step와 bank/ref는 추출됨. duration0/-1의 wrap 및 event에 의한 전환이 있어 단순 합계/FPS로 실제 애니메이션 속도를 단정하지 않음.',
            '정적 시각 검토에서 없다고 판단한 문제도 실제 연속 동작·배경·장면 전환의 모든 결함 부재를 보증하지 않음.'],
          'next_actions':['리코 벽 수정 후보의 독립 재디코드/빌드 후 벽 슬라이드·벽 공격을 실기 확인'] if ch=='riko' else ['현재 린 도트 보존. 이후 구체적 실기 제보가 있으면 해당 bank/ref로 추적'],
          'game_inputs_modified':False,'game_bin_written':False,'emulator_save_pointer_modified':False}
        write(base/'report.json',report);reports[ch]=(base/'report.json').relative_to(ROOT).as_posix()
    write(WORK/'report.json',{'status':'static_export_visual_audit_complete','reports':reports,
        'confirmed_changes_prepared':['riko_wall_head_height'],'rin_new_changes':[],
        'wall_verification':'work/sprite_consistency_20261105/zero/riko/wall_fix/verification.json',
        'runtime_verified':False,'source_inputs_preserved':True})
    (WORK/'REPORT.md').write_text('''# 제로 계열 일관성 감사

실제 최신 BIN에서 리코·린 각각 압축 참조444개를 추출했다. 436개는 독립 프레임,8개는 이전 VRAM이 필요한 부분 갱신이다. 낙봉파 내장 몸체2개를 추가해 manifest는446항목이며 일반/블랙 각각438장이다.384×384 캔버스의 원점(160,160)을 유지했다. 동작을 맞추려고 임의 확대하거나 중심을 다시 잡지 않았다.

각 캐릭터62개 전체 비교 시트와26개 몸체 전용 비교 시트(315참조)를 마련했다. 몸체 전용 시트는 원래 픽셀을 그대로 쓰고 큰 순수 효과만 제외해 대기 옆에서 읽기 쉽게 만든 것이다. 실제 열람 범위와 모든 파일 목록은 각 report.json에 있다. Black은 별도 이미지가 아니라 실제 row13 색상의 공유 비트맵이다. 대표 대기/벽을 직접 확인했으며 Black 전 프레임의 별도 육안 감사까지 마쳤다고 하지는 않는다.

확정 수정은 리코 벽38~43 및 같은 머리를 공유하는 벽 공격10개다. 대기147/벽35~37의 머리색 영역22×18(188px)에 비해22×14(143px)로 납작했다. 대기 측정은 몸의 같은 색1픽셀을 제외하는 y<-5 머리 ROI로 정정했다. 새23×20 머리를 목 기준(0,-3)에 넣고 기존 손·팔·어깨·몸·무기·발은 전부 보존했다. root가 수정 후보 전체 비교를 직접 보고 채택했다. 실제 게임 적용·사용자 실기 수용은 이 감사 범위에 포함하지 않는다.

린은26개 몸체 비교 시트를 직접 보았고 강제로 바꿀 정도로 명확한 새 일관성 결함을 찾지 못했다. 리코 지상 베기 후반의 넓은 흰 부츠 면은 선택적 추가 검토 사항이며 결함으로 확정하지 않았다. 승리 측면의 얇은 다리, 회전·웅크림 시 작은 전체 높이는 포즈 변화와 구별해야 한다.

리코 준비 ARC는36e231a882be87d71d603667a26909025003b88908f939f115d328b0dd4d53dc이다. 동일 입력 재생성이 바이트 단위 일치했고 원래 머리로 무변경 왕복도 원본 ARC와 동일하다. 대상16개 이외428참조(420개 전체표시+8개 부분raw), 대기147, 조립/팔레트/음향/정적 그림/타이밍이 보존됐다. 모든 타일 수는 원래대로이며 최대32개다.7종 잘못된 입력은 출력 전에 거부됐다. 근거는 wall_fix/verification.json에 있다.

현재 실기 CLUT, 별도 효과 호출/색, 부분 VRAM42~49의 전후 문맥은 정적 추출만으로 확정할 수 없다. 정확한 애니메이션 raw 타이밍과 이벤트는 보존했지만 단순 합계의60FPS 영상이 원작 동작이라고 주장하지 않는다. independent coverage 증거는 ../coverage/REPORT.md에 있다. 입력 BIN·에뮬레이터·F1·메모리카드·현재 포인터는 이 작업에서 변경하지 않았다.
''',encoding='utf-8')
    print(json.dumps(reports))


if __name__=='__main__':
    main()
