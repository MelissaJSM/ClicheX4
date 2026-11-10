"""Read-only reconstruction of the historical PL00 departure silhouette recipe."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sys.path[:0]=[str(ROOT),str(W/'nana_audit/native_restore')]
from preview_restore import Archive
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=W/'root_nana_hover/packed_hover_final01/PL00_U.ARC'
assert sha(src)=='9c1ff453a2308ddc40f39e5790de0aa6a5cf41dda43165b0fa16808f8c3a643c'
recipe=ROOT/'scripts/prepare_nana_air_clone_art.py'
assert 'np.rint(74+(xs-74)*.45)'in recipe.read_text('utf8')
a=Archive(src.read_bytes());idle=a.layer(0,0)[0];current=a.layer(210,0)[0]
# Original canvas origin80, beam center74 => worldX -6. Current canvas origin160.
ys,xs=np.nonzero(idle);v=np.zeros_like(idle);xx=np.rint(154+(xs-154)*.45).astype(int);v[ys,xx]=9
report={'read_only':True,'candidate':src.relative_to(ROOT).as_posix(),'candidate_sha256':sha(src),'recipe':recipe.relative_to(ROOT).as_posix(),'recipe_sha256':sha(recipe),'original_canvas_origin':[80,80],'original_beam_center_x':74,'world_beam_center_x':-6,'horizontal_factor':0.45,'method':'非透明 source pixels forward-scattered with numpy.rint, collisions merged; not nearest-resize of a bounding box','source_ref':0,'destination_ref':210,'source_opaque_pixels':int((idle>0).sum()),'reconstructed_opaque_pixels':int((v>0).sum()),'current_opaque_pixels':int((current>0).sum()),'pixel_difference':int((v!=current).sum()),'recipe_exact_current':bool(np.array_equal(v,current)),'runtime_verified':False,'game_assets_changed':False,'limits':['기본형의 역사적 산출 규칙 확인이며 포스아머별 분리 가능성/실제 renderer 호출 여부는 별도 조사다.']}
out=W/'root_nana_clone210_source01';out.mkdir(exist_ok=False)
(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(report,ensure_ascii=False))
