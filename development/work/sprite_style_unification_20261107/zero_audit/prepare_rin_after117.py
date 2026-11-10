"""Record actual remaining-art review and prepare the next four authored poses."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank
D=Path(__file__).parent/'rin_extension';P=D/'prepared_hurt_lowhp_v1/PL01_U.ARC'
sha=lambda b:hashlib.sha256(b).hexdigest()
rel=lambda p:str(p.relative_to(ROOT))
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
arc=P.read_bytes();assert sha(arc)=='4e18b1cda6731f97272eba361a2ac19df3606f75a19b5352f6025d403196e769'
pal=struct.unpack_from('<16H',entry(arc,9));bank=graphics_bank(entry(arc,2),0)
displays={n:render(arc,0,0,n)[0]for n in range(len(bank['frames']))}
reviewdir=D/'remaining117_review';mp=reviewdir/'manifest.json';review=json.loads(mp.read_text('utf8'))
assert review['source_sha256']==sha(arc)
notes={
 'air_saber':'18개 모두 실제 열람.236..240을 포함해 머리의 큰 흰 면과 단순한 커프·앞치마가 대기보다 거칠다. 자세·검기 접점이 달라 각도별 원화가 필요하다.',
 'air_spin':'9개 접힌 회전 자세는 실루엣 자체가 정상이나 머리·부츠·치마 면이 섞여 읽힌다. 정지 대기 머리를 회전해 붙이지 않고 각 회전 각도를 새로 그린다.',
 'arrival_body':'249/251 중심의 얼굴·의상 단순화가 남아 있다.247/248은 원래 빛 형상으로 몸체 명암 부족 결함으로 세지 않으며 새 본체와 파생 관계를 조사한다.',
 'ground_saber':'가장 먼저 고칠 군. 새61과 이전62/63/65/67에서 머리·옷깃·커프·부츠의 상세도가 달라진다.67/69 및73/75/77/79/81은 각각 완전히 같은 표시다. 새 대표 원화를 공유할 수 있다.',
 'hyouretsuzan':'6개 독립 본체의 머리·소매·부츠가 단순하다.별도 무기 객체의 VRAM 합성은 이 본체 시트에 포함되지 않는다.',
 'idle':'0/1/2/146과147/148은 수용 대기 호흡·깜박임 기준.무조건 새 그림 대상에 넣지 않는다.',
 'ladder':'사다리 후면은 이미 새 그림.남은197/199/202 계열은 옆면 연결/공격 자세이며 소매·치마·부츠 명암이 단순하다.3개 키로9개 동일 표시 참조를 대응할 수 있다.',
 'raijingeki_shared':'뇌신격의 준비/돌진/복귀 공유 몸체.가슴과 치마가 넓은 단색 면이고 일부 머리는 대기보다 작은 공 모양이다.88은 섬광이므로 원화 본체와 분리한다.',
 'rakuhouha':'새182..185와 그 전후177..181/186..189의 머리·커프·치마 상세 차이가 남아 있다.원래 에너지 구체/방출부는 보존하고 본체만 갱신해야 한다.',
 'rakuhouha_static_body':'정적23/24는 이전52 이후 갱신되어 현117에도 보존된다.메인 장부에 새 원화참조로 계산하지 않아 남은 칸에 보일 뿐, 미작업으로 해석하지 않는다.',
 'ride_armor_head':'19개 독립 머리 표시를 모두 봤다.크기·각도는 조종석 가림과 함께 검토해야 한다.옆면의 머릿결과 얼굴 명암이 대기보다 적으므로 동일 각도·표정 원형 공유를 조사해 갱신한다.',
 'ride_chaser':'28개 모두 머리·가슴띠·부츠가 큰 단색 면에 가깝다.기울기별 본체와 망토 변형 관계를 먼저 분리하면 다수 원화를 따로 생성할 필요를 줄일 수 있다.탑승 접점과 차량 자체는 미포함이다.',
 'run':'7..20 새 달리기와 이어지는3/4만 오래된 큰 볼·단순 커프가 남았다.5/6은 수용 대기의 동일 표시 여부를 별도 검사하여 유지한다.',
 'ryuenjin':'상승 회전148/150/152/154는 완료.144/146의 준비와156/158의 복귀 몸체에 단순 머리·소매·부츠가 남는다.불꽃은 변경 없이 별도 보존한다.',
 'shippuuga':'대시공격 준비155/156/158 및 회전160..172는 대기와 다른 둥근 얼굴·큰 단색 의상 면이 남는다.회전 관점 차이는 보존하면서 상세 묘사를 새로 만든다.',
 'victory_return_body':'b1_0은 수용 대기와 같은 복귀 정지형인지 exact 검사한다.현재 새1..8과 섞인 전체 완성 의미로 세지 않는다.',
 'wall_saber':'4개 키50/51/54/57의10참조 모두 동일 계열.새 벽39와 머리·커프·부츠 묘사가 크게 달라진다.원벽손/짧은 자루 및 검기 연결을 지키며 네 키를 새로 그리면 된다.'
}
for g in review['groups']:
 g['visual_observation']=notes[g['group']]
 for s in g['sheets']:
  p=ROOT/s['path'];assert sha(p.read_bytes())==s['sha256'];s['actually_viewed']=True
review.update(full_visual_review_complete=True,review_scope='최신117 작업 ARC의 잔여196개 메인 본체/머리 참조를 정확 동일 표시153개로 묶은 일반색32장 실제 열람.일반/레드 양색 전수 실기나 신규원화 완료를 뜻하지 않는다.',normal_sheets_actually_viewed=32,black_remaining_sheets_viewed_in_this_review=0,static_body_refs_already_synced=['static_23','static_24'])
idleids=[0,146,147,148]
identity=[]
for b,n in [(0,5),(0,6),(1,0),(1,86)]:
 a=render(arc,b,b*5,n)[0]
 identity.append({'key':f'b{b}_{n:03}','identical_idle_refs':[k for k in idleids if np.array_equal(a,displays[k])]})
review['idle_exact_comparison']=identity
review['priority']=[
 {'order':1,'keys':['b0_062','b0_063','b0_065','b0_067'],'next':'b0_071/073 및 다음 지상 공격','reason':'새61 직후 머리·커프·치마·부츠의 단순한 묘사가 연결되어 가장 먼저 눈에 띈다.'},
 {'order':2,'keys':['b1_050','b1_051','b1_054','b1_057'],'expansion_refs':10,'reason':'새벽 본체와 오래된 벽 공격 질감 차이가 크고 정확 동일 표시 공유가 많다.'},
 {'order':3,'keys':['b0_003','b0_004','b0_249','b0_251'],'reason':'이동 진입과 등장/준비 연결의 남은 오래된 표현.'},
 {'order':4,'groups':['air_saber','shippuuga','raijingeki_shared','ryuenjin','rakuhouha','hyouretsuzan'],'reason':'공격의 정지 대기 대비 머리·커프·의상 명암 차이, 원무기/불꽃 접점 분리 필요.'},
 {'order':5,'groups':['ride_chaser','ride_armor_head','air_spin','ladder'],'reason':'탑승/회전은 동일 각도·표정 공유와 가림 제약 확인 후 새 묘사 확장.'}]
dump(mp,review)
lines=['# 린117 이후 남은 미술 검토','',review['review_scope'],'','신규 원화·파생 효과까지 누적117참조가 준비됐으며 전수 완료·사용자 수용·실기 완료는 아니다. 대기 및 정확 동일 사본은 보존 대상으로 구분한다.','']
for g in review['groups']:lines.extend([f"- **{g['group']}**: {g['visual_observation']}"])
lines.extend(['','다음 입력은 지상 공격62/63/65/67 네 키. 변경 전 실제 손·발·검기 위치, 파츠와 공유 스트림을 기록하고 기존 동작 자체를 바꾸지 않는다.','',f'대기 exact 검사: `{json.dumps(identity,ensure_ascii=False)}`',''])
(reviewdir/'REVIEW.md').write_text('\n'.join(lines),'utf8')
out=D/'ground_first01';assert not out.exists();out.mkdir()
crop=(112,112,208,208);refs=[62,63,65,67];native=Image.new('RGBA',(192,192));records=[]
ap=ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/zero_animations.json';animations=json.loads(ap.read_text('utf8'))['animations']
for i,n in enumerate(refs):
 a=displays[n];pic=rgba(a,pal);outside=a.copy();outside[112:208,112:208]=0;assert not np.any(outside)
 native.paste(pic.crop(crop),(i%2*96,i//2*96));Image.fromarray(a).save(out/f'b0_{n:03}_before_indices.png')
 f=bank['frames'][n]
 records.append({'key':f'b0_{n:03}','bank':0,'ref':n,'cell':[i%2,i//2],'bounds':pic.getbbox(),'source_canvas_sha256':sha(a.tobytes()),'exact_display_expansion_refs':[k for k,v in displays.items()if np.array_equal(a,v)],'same_stream_refs':[g['index']for g in bank['frames']if g['offset']==f['offset']],'tile_count':f['tile_count'],'native_animation_uses':[q for q in animations if q['graphics_bank']==0 and any(s['frame']==n for s in q['steps'])]})
native.save(out/'native_input.png');native.resize((1536,1536),Image.Resampling.NEAREST).save(out/'input.png')
for label,n in [('idle147',147),('refined_attack61',61),('refined_third111',111)]:rgba(displays[n],pal).crop(crop).resize((768,768),Image.Resampling.NEAREST).save(out/f'{label}.png')
dump(out/'inputs.json',{'actual_input_arc':rel(P),'archive_sha256':sha(arc),'source_bin':'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin','source_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','character':'rin','crop':crop,'native_cell':[96,96],'columns':2,'rows':2,'scale':8,'native_origin':[160,160],'palette_words':list(pal),'frames':records,'animation_evidence':rel(ap),'animation_evidence_sha256':sha(ap.read_bytes()),'generated':False,'game_unchanged':True})
prompt='''Use case: precise-object-edit. Edit only the first FOUR-POSE sheet, retaining its exact2x2 layout, cell positions and all four different attack motions. Character is Rin, a white bob-haired blue-and-white maid with cyan eyes. The other images are approved detailed native style references, not replacement poses. Repaint the coarse first-sheet sprites into the same carefully clustered pixel-art quality as idle147 and the two approved attack references: separated cool-gray hair locks and face planes, small cyan eye, selective navy outline, collar/ribbon details, cuff folds, apron straps/seams, pleated skirt hem and boot shading. Preserve exact original head/eye center, short neck, shoulders, elbows, gloves, gripping hands, tiny existing short tool connection, hips, knee angles, planted boot toe/heel contacts, figure scale and center. These are ground sword-swing body poses; do not invent a new long sword or broom or an aura. The hand/tool/effect attachment positions must not drift. Keep upper-arm/waist/thigh/calf thickness consistent with the reference, no pin-thin support legs or broad round baby face. Do not simplify the garment to large plain colored areas. Use purposeful native pixel clusters, not blur or added texture noise. All four source poses must remain individually recognizable. Native cell96x96 presented at8x nearest-neighbor; preserve fixed blank margins and output a1536x1536 sheet of exactly FOUR sprites. Transparent background, no lettering, grid, labels, extra icons, floor, shadows, effects or environment. Do not paste an idle body or change facing direction. Upper-left begins the overhead swing, upper-right reaches its forward glove, lower-left opens the arms, lower-right completes the lowered forward-leaning follow-through. Keep both feet planted exactly as in each source.'''
(out/'prompt.txt').write_text(prompt+'\n','utf8')
print(json.dumps({'sheets_viewed':32,'idle_identity':identity,'next':rel(out),'keys':refs},ensure_ascii=False))
