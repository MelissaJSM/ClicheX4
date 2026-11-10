from pathlib import Path
import sys,json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
sha=lambda b:hashlib.sha256(b).hexdigest()
D=W/'x_vehicle_review01';manifest=json.loads((D/'manifest.json').read_text('utf8'))
discs={}
for char,mode,ver,stem,digest in [('shibuki','ver_buki_riko',14,'shibuki_riko','b1e00232f8a62bea766e7b40dded110b0c2e66a2fbd2795725347510a0af581d'),('nana','ver_rin_nana',16,'rin_nana','c2972d3552214336316f0e2d85d96f8f66ac50b470a423dbba47cda994258e78')]:
    p=ROOT/f'out/{mode}/sprite_style_unification_20261107_v{ver}/{stem}.bin';assert sha(p.read_bytes())==digest
    extracted=read_disc(p,('PL00_U.ARC','PL02_U.ARC'))[0]
    for name,data in extracted.items():assert sha(data)==manifest['sources'][char+'/'+name]['sha256']
    discs[char]={'path':p.relative_to(ROOT).as_posix(),'sha256':digest,'arc_readback_exact':True}
for p in manifest['pages']:assert sha((ROOT/p['path']).read_bytes())==p['sha256']
r={'scope':'두 X의 차량/노바/호버51참조×4폼=408표시를22판으로 실제 열람. 중복은 정확 RGBA 별칭으로만 묶음.',
   'root_actually_viewed':manifest['pages'],'current_discs':discs,
   'source_manifest_sha256':sha((D/'manifest.json').read_bytes()),
   'findings':[
       {'character':'shibuki','refs':'162..174','decision':'세부 묘사 보완','detail':'전폼에서 앞머리가 밝은 큰 면으로 단순하고 소매/가슴/옆머리 층이 대기보다 적다. 앉은 체형 및 손/좌석 기준점을 보존한 재작화 대상.'},
       {'character':'shibuki','refs':'184..203','decision':'머리 전용 보존 + 장식 국소 확인','detail':'몸체 없는 라이드아머 머리이며198은 빈 참조로 보인다. Ultimate 대기의 금색 장식과 비교해 작게 보이는 장식의 위치/식별성을 후속 대조. 몸체/기체를 임의로 추가하거나 전신 높이로 늘리지 않는다.'},
       {'character':'shibuki','refs':'213..230','decision':'몸체 상세 보완, 효과 분리','detail':'213..216과221..230의 얼굴/소매/가슴은 대기보다 단순하다. 217/220은 몸과 효과, 기본/포스218/219는 효과만, Ultimate218은 몸과 효과·219는 효과다. 같은 번호라고 같은 편집 범위를 가정하지 않는다.'},
       {'character':'nana','refs':'162..174','decision':'기본/포스 우선 상세 보완','detail':'기본/포스 뒷머리가 거의 단색 띠로 줄고 상의도 단순하다. Ultimate의 색 층은 상대적으로 남아 있으나 새 대기 수준과 비교해 사지/상체 묘사를 이어서 검토한다. 원래 탑승 접점과 앉은 자세 유지.'},
       {'character':'nana','refs':'184..203','decision':'현재 머리 전용 그림 보존','detail':'베레모/포스 베일/Ultimate 토끼귀를 구별할 수 있고 이번 열람에서 새 확정 절단을 찾지 못했다. 작은 얼굴 전용 스프라이트로 전신과 단순 높이 비교하지 않는다.'},
       {'character':'nana','refs':'213..230','decision':'몸체 상세 보완, 효과 분리','detail':'기본/포스213..216 및 호버221..230의 뒷머리·의상 큰 단색 면을 보완. Ultimate의 회색 신발/종아리와 머릿결도 대기 묘사 기준으로 재검토. 사랑이 총구/추진 발위치/기존 이펙트 보존.'}
   ],
   'limits':['Ultimate217..230은 원래 렌더러에 맞춰mask15로 합성한다. 캡슐 전 해당 능력 도달 불가는 별도이며 전후폼 그림이 같은 것만으로 실행 결함이라고 판정하지 않는다.',
             '기본형은 전용 아머 능력에 도달하지 않는다. 정적 자원 표시는 실제 모든 폼에서 사용됨의 증거가 아니다.',
             '정적 열람과 후보 분류이며 이번에 새 그림/게임 적용/실기 완료나 사용자 수용을 하지 않았다.'],
   'all_art_complete':False,'game_or_art_modified':False}
p=W/'root_review_checkpoint72.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p.read_bytes()))
