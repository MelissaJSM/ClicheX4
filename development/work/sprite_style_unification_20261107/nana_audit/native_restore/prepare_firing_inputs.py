"""Prepare four read-only image references per costume; does not generate art."""
from preview_restore import *

def main():
 assets,_=data();directory=OUT/'moving_fire_inputs';directory.mkdir(exist_ok=True);forms=[('base','PL00_U.ARC',0,'nana(X).webp'),('fourth','PL00_U.ARC',15,'nana(4th armor).webp'),('jacket','PL02_U.ARC',15,'nana(ultimate armor).webp'),('swimsuit','PL02_U.ARC',0,'nana(ultimate armor).webp')];manifest={'parent_sha256':EXPECTED,'new_art_generated':False,'forms':[]}
 for form,name,mask,concept in forms:
  a=Archive(assets[name]);folder=directory/form;folder.mkdir(exist_ok=True)
  helper.grid([(form,[('대기 기준 0',a.composite(0,mask)[0])])],folder/'01_idle.png',6)
  helper.grid([(form,[('정지 사격 85',a.composite(85,mask)[0])])],folder/'02_standing_fire.png',6)
  rows=[]
  for n in(2,8,16,26):rows.append((f'ref {n}',[('해당 보행',a.composite(n-1,mask)[0]),('현 이동사격',a.composite(n,mask)[0])]))
  helper.grid(rows,folder/'03_moving_fire_poses.png',5)
  ref=ROOT/'character/ver_rin_nana'/concept
  manifest['forms'].append({'form':form,'archive':name,'arc_sha256':sha(a.data),'mask':mask,'four_references':[{'path':(folder/n).relative_to(ROOT).as_posix(),'sha256':digest(folder/n)}for n in('01_idle.png','02_standing_fire.png','03_moving_fire_poses.png')]+[{'path':ref.relative_to(ROOT).as_posix(),'sha256':digest(ref)}],'constraints':['현재 눈·어깨·손·권총·총구·발 원점과 동작 타이밍을 유지한다.','대기에서 읽히는 머리결·안면·옷의 경계/중간명암을 팔을 뻗은 실제 포즈로 다시 그린다.','정지 사격 소매를 수평으로 늘리거나 단색 띠로 채우지 않는다.','얼굴·다리를 옛 단순 도트로 덮지 않는다. 새 생성물 전체를 대기 기준에서 검수한다.','게임 팔레트와 32타일 제약은 생성 후 검증하며, 제약을 이유로 디테일 통일 완료라고 하지 않는다.'],'muzzle_alignment':'기존 네이티브 위치 보존. 새 그림 등록 시 손/권총 및 총구 픽셀 좌표를 기존값과 대조해야 함.'})
 write(directory/'manifest.json',manifest)
 (directory/'REQUEST.md').write_text('''# 나나 이동사격 후속 그림 입력

현재 단계에서는 그림을 생성하지 않았다. 각 폼에 대기, 정지 사격, 보행/이동사격 네 포즈 묶음, 사용자 설정화의 네 입력을 준비했다. 설정화는 원본 경로를 참조하며 복사·수정하지 않았다.

현재 이동사격은 정지 팔의 좁은 스트립을 가로로 늘려 만든 구간 때문에 소매/손목 또는 맨팔이 긴 띠로 읽힌다. 기존 원화에 없는 굽힘과 재질 구획을 복원할 수 없으므로 새 포즈 그림이 필요하다. 원화 재등록만으로 해결됐다고 보고하지 않는다.

먼저 기본형 한 동작 묶음(2, 8, 16, 26)의 어깨~손목~사랑이 연결을 그린다. 사용자가 수용한 대기의 얼굴/머리결/의상 명암과 같은 밀도를 목표로 한다. 기존 총구와 손 기준점, 전신 높이와 발 접점은 입력의 네이티브 원점을 따른다. 팔·소매가 길어 보인다고 탄환 발사 위치를 이동하지 않는다.

포스는 소매가 달라 별도 의상 해석이 필요하고, 수영복은 맨팔이므로 기본형의 소매 텍스처를 붙이지 않는다. 재킷은 현재 재킷의 팔 디자인을 사용한다. 네 폼을 동시에 생성하지 않는다.
''','utf8')
 print(json.dumps({'forms':len(manifest['forms']),'inputs':str(directory.relative_to(ROOT))}))

if __name__=='__main__':main()
