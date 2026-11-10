"""Read-only source/hand-window provenance for Nana arrival133,135,136,137."""
from pathlib import Path
import hashlib, json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.export_x_consistency import Archive

D = Path(__file__).parent
O = D / 'nana_ultimate_ceremony_pistol_sources01'
O.mkdir(exist_ok=True)
N = D.parent / 'nana_audit'
F = ROOT / 'work/overhaul_20261105/sprites/nana_preultimate'
EARLY = ROOT / 'work/ver_rin_nana/nana_art/arrival_v1'
JACKET = ROOT / 'work/ultimate_costume_swap_20261105/core/arrival_v1/ver_rin_nana'
tracked = {}
sha = lambda b: hashlib.sha256(b).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
def read(p):
    b = p.read_bytes()
    tracked[rel(p)] = sha(b)
    return b
def meta(p): return json.loads(read(p))
def img(p):
    read(p)
    return Image.open(p)
def bbox(m):
    y, x = np.nonzero(m)
    return [int(x.min()-160), int(y.min()-160), int(x.max()-159), int(y.max()-159)] if len(x) else None

arcpath = N / 'ultimate_hurt_repaint/packed_hurt_candidate_v1/PL02_U.ARC'
arcbytes = read(arcpath)
assert sha(arcbytes) == 'c9e68442829a7f149ae86317c88172e27dbce545e454687b98310fad28ef83a5'
a = Archive(arcbytes)
early_meta = meta(EARLY / 'production02/art.json')
jacket_meta = meta(JACKET / 'registered_v1/registration.json')
state = meta(F / 'state_overrides/state.json')
for p in [EARLY/'generated.png', EARLY/'prompt.txt', F/'arrival_generated.png', F/'arrival_prompt.txt',
          JACKET/'generated.png', JACKET/'prompt.txt', ROOT/'scripts/normalize_nana_arrival.py',
          ROOT/'scripts/overhaul_sprites_state_layers.py', ROOT/'scripts/ultimate_arrival_jacket.py',
          ROOT/'scripts/prepare_nana_fourth_ceremony_art.py', ROOT/'scripts/prepare_nana_ultimate_ceremony.py']:
    read(p)

font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 14)
refs = [133,135,136,137]
window = [-26,-36,28,26]
scale = 5
w, h = (window[2]-window[0])*scale, (window[3]-window[1])*scale
sheet = Image.new('RGB', (3*(w+16), 4*(h+38)), '#252d38')
draw = ImageDraw.Draw(sheet)
rows = []
for ri, n in enumerate(refs):
    oldpic = img(EARLY/f'production02/frame_{n:03}.png').convert('RGBA')
    oldcan = Image.new('RGBA',(384,384)); oldcan.alpha_composite(oldpic,(80,80))
    base = a.layer(n,0)[0]
    stored = np.array(img(F/f'state_overrides/base_{n:03}.png'))
    assert np.array_equal(base, stored), n
    overlay = np.array(img(JACKET/f'registered_v1/overlay_{n:03}.png'))
    overlaycan = np.zeros((384,384),np.uint8)
    overlaycan[80:80+overlay.shape[0],80:80+overlay.shape[1]] = overlay
    assert np.array_equal(a.layer(n,5)[0], overlaycan), n
    jr = next(x for x in jacket_meta['masters'] if x['frame']==n)
    hands = [[q-80 for q in box] for box in jr['head_hand_foot_regions']['hands']]
    windows = []
    for box in hands:
        x,y,x2,y2 = [q+160 for q in box]
        m = np.zeros_like(base,dtype=bool); m[y:y2,x:x2] = True
        values, counts = np.unique(base[m],return_counts=True)
        windows.append({'world_rect_exclusive':box, 'base_opaque_pixels':int(np.count_nonzero(base[m])),
                        'base_index_counts':dict(zip(map(int,values),map(int,counts))),
                        'overlay5_nonzero_in_protected_window':int(np.count_nonzero(a.layer(n,5)[0][m]))})
        assert not np.any(a.layer(n,5)[0][m])
    items = [('초기 기본형 등록 / 자세 근거',oldcan),('현재 Ultimate 재킷 / 손창 표시',a.composite(n,15,2)[0]),('현재 맨팔 / 손창 표시',a.composite(n,0,2)[0])]
    for ci,(label,pic) in enumerate(items):
        x,y = ci*(w+16),ri*(h+38)
        draw.text((x+4,y+3),f'{n} {label}',font=font,fill='white')
        crop=pic.crop(tuple(v+160 for v in window)).resize((w,h),Image.Resampling.NEAREST)
        sheet.paste(crop,(x,y+30),crop)
        if ci:
            for wi,box in enumerate(hands):
                rect=[x+(box[0]-window[0])*scale,y+30+(box[1]-window[1])*scale,
                      x+(box[2]-window[0])*scale-1,y+30+(box[3]-window[1])*scale-1]
                draw.rectangle(rect,outline='#35d7ff' if wi==0 else '#ffd33c',width=1)
    early = next(x for x in early_meta['registrations'] if x['frame']==n)
    rows.append({'ref':n,'initial_registered_source':early,
                 'initial_native_png':rel(EARLY/f'production02/frame_{n:03}.png'),
                 'current_direct_source':rel(F/'arrival_generated.png'),
                 'current_base_exact_state_override':True,'current_overlay5_exact_registered_jacket':True,
                 'whole_body_registration':next(x for x in state['arrival_registration'] if x['frame']==n),
                 'historical_jacket_hand_protection':windows,
                 'dedicated_pistol_mask_or_muzzle_anchor_in_these_scripts':None})
sheetpath=O/'initial_current_hand_windows.png';sheet.save(sheetpath)

# Preserve the two source atlases for review via hashes and original locations;
# this code does not copy or edit source artwork.
for p,hsh in tracked.items(): assert sha((ROOT/p).read_bytes()) == hsh
report={
 'scope':'Nana133/135/136/137의 최초 권총 자세, 현재 전신 재등록 출처, 재킷 손 보호창을 읽기 대조했다. 원화·ARC·게임 수정이나 제작 함수 호출 없음.',
 'candidate_arc':rel(arcpath),'candidate_arc_sha256':sha(arcbytes),
 'coordinate_convention':'세계 원점0,0. 원160캔버스의80을 빼며 끝좌표는 exclusive. 손 보호창은 권총 전용 마스크가 아니다.',
 'sources': [{'path':p,'sha256':h} for p,h in tracked.items()],
 'frames':rows,
 'source_chain_finding':[
   '초기 arrival_v1/generated.png에는133의 낮춘 권총,135의 가슴 앞 권총,136의 턱 옆 권총,137의 머리 위 권총이 실제로 보인다. prompt도 이를 명시한다.',
   '현재 직접 선행원화 nana_preultimate/arrival_generated.png의 네 자세에는 구분 가능한 권총이 보이지 않는다. arrival_prompt는 맨손 자세/의상 변경을 지시하고 사랑이 유지 요구는 명시하지 않았다.',
   'complete_effects는 해당 전신을 눈·바닥 기준으로 재등록하고136/137의 흰 tile7 효과만 합쳤다. 최초 권총 창을 별도로 복원하거나 고정하는 코드가 없다.',
   '현재 base0가 그 state_overrides PNG와 네 참조 모두 exact임을 확인했다. 현재 재킷 overlay5도 당시 registered_v1과 exact이다. 손 보호창에는 overlay5가0이므로 재킷층이 기존 완성 권총을 지운 문제로 볼 근거가 없다.'
 ],
 'recommendations':[
   '현재 손·소매의 어두운 덩어리 전체를 완성된 사랑이로 복사하지 않는다. 현재133..137에서 정본8px 권총을 추출했다는 주장도 피한다.',
   '최초 원화의 권총 방향/순서와 새 손의 실제 접점을 기준으로 수용된 사랑이 모듈을 국소 정합한다. 최초 기본형과 현재 Ultimate의 몸체 크기·손 좌표는 다르므로 초기 좌표를 그대로 붙이지 않는다.',
   '136/137의 원46px 흰 선은 독립 tile7 효과다. 새로운 총구와 강제로 맞추거나 위치를 이동할 근거가 없으며 원래 위치와 원시간표를 보존한다.',
   '133/135/136/137의 정확한 새 총구·그립 좌표는 신규 등록 후 정해야 한다. 여기 기록된 손창과 초기 source_box를 최종 권총 의미 마스크로 오해하지 않는다.'
 ],
 'sheet': {'path':rel(sheetpath),'sha256':sha(sheetpath.read_bytes()),'window_world':window,'scale':scale,'actually_viewed':False},
 'actual_original_images_viewed':[rel(EARLY/'generated.png'),rel(F/'arrival_generated.png')],
 'limits':['현재 native 권총의 독립 의미 마스크/정확한 총구 좌표는 확인되지 않았다.',
           '새133..137 권총의 미술 수용·원순서 재생·게임은 이 읽기 조사에 포함하지 않는다.'],
 'producer_functions_called':False,'runtime_verified':False}
out=O/'report.json'
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'path':rel(out),'sha256':sha(out.read_bytes()),'sheet':rel(sheetpath)},ensure_ascii=False))
