from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];out=W/'root_review_checkpoint151.json';assert not out.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[D/f'packed_hover_final01/readback_{n}.png'for n in(221,223,225,227,229)]
files += [D/f'native_cycle01/timeline_{n}.png'for n in[*range(21,27),*range(133,139)]]
files += [D/f'rearfoot_registered01/comparison_{n}.png'for n in(229,230)]
files += [D/f'rearfoot_jet_probe02/{name}_{n}.png'for name in('jets','partials')for n in(229,230)]
assert len(files)==23 and all(p.exists()for p in files)
cp=D/'packed_hover_final01/PL00_U.ARC';assert sha(cp)=='9c1ff453a2308ddc40f39e5790de0aa6a5cf41dda43165b0fa16808f8c3a643c'
r={'checkpoint':151,'candidate_sha256':sha(cp),'actually_viewed_files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'actually_viewed':True}for p in files],
'observations':['기본/포스 새 호버10참조 재추출5판에서 승인대기·옛그림·새그림을 직접 비교했다. 머리카락/검은 옷/베일의 명암을 복구했고 추가 확정 몸통/팔 연결 절단을 찾지 못했다.','12개 원순서 정적판을 직접 열람했다. 연결공중45..48은 기존부모이며 새호버221..230만 바뀌었다. 제시된 순서에 추가 확정 큰 크기 도약을 찾지 못했다.','229/230의 굽힌 종아리·신발20셀을 별도 새원화에서 보완했다. 다른층·ROI밖·직선다리·최저발Y를 유지하며 16부분조합과 고정jet12..14 정적판에서 신발 위치/불꽃 연결을 확인했다.','기존 첫안도 피부/무릎이 불꽃alpha에 겹쳤으므로 단순 거리0으로 신발 접점이 맞다고 판단하지 않는다. 새신발의 윤곽과 검정/자주색을 직접 비교했다.'],
'machine_evidence':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in[D/'packed_hover_final01/verification.json',D/'packed_hover_final01/reproduction.json',D/'native_components01_native_checks.json',D/'native_cycle01/verification.json']],
'limits':['원순서12판은 기본+다리 표시의 정적 전환이며 포스의 모든 전환을 인간이 재생 관찰했다고 확대하지 않는다. 포스10은 별도재추출5판 및84canvas 중 포스28canvas로 확인했다.','불꽃은 원위치의 중립색 진단이며 실제CLUT·반투명·60Hz·입력·부분아머 실기는 미실행이다.','원MIPS15참조와7296RGBA/50층/비대상보존은 기술검사이며 전체미술 완성/사용자 수용과 별개다.'],
'root_static_art_direction_accepted':True,'runtime_verified':False,'whole_project_complete':False}
out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'review':151,'directly_viewed':len(files),'sha256':sha(out)}))
