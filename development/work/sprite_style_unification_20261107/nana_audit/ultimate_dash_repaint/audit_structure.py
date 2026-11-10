"""현재 동결 PL02의 대시 효과·별개 연결 동작·노바 의존성을 읽기 감사한다."""
from pathlib import Path
import sys,json,copy
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
from src.psx_player import composition_frame,compose_indices
from prepare_inputs import SRC,EXPECTED,merged
def semantic(parts):return [{k:p[k]for k in('flags','tile','x','y')}for p in parts]
def main():
 need(digest(SRC)==EXPECTED,'Parent');a=Archive(SRC.read_bytes());out=D/'structure_v3';out.mkdir(exist_ok=False);effects=[]
 prior_path=N/'dash_repaint/effects/manifest.json';prior=json.loads(prior_path.read_text('utf8'))
 for original,n in((71,73),(72,74)):
  cp=composition_frame(a.c,0,n);base=composition_frame(a.c,0,original);a.layer(n);f=a.banks[0]['frames'][n];raw=a.raw[f['offset'],f['tile_count']].data
  equal=semantic(cp['parts'][:len(base['parts'])])==semantic(base['parts'])
  q=next(q for q in prior['frames']if q['ref']==n)
  extra=copy.deepcopy(cp);extra['parts']=q['parts'];need(len(extra['parts'])==9,'Historical9 effects')
  pix,size,box,_=compose_indices(raw,f['tile_count'],extra,allowed_cluts={0});small=np.frombuffer(pix,np.uint8).reshape(size[1],size[0]);fx=np.zeros((384,384),np.uint8);yy,xx=np.nonzero(small);fx[yy+box[1]+160,xx+box[0]+160]=small[yy,xx]
  need(sha(fx.tobytes())==q['effect_sha256'],'Current tile6 equals historical54texel effect')
  body=a.layer(original)[0];cur=a.layer(n)[0];rebuilt=body.copy();rebuilt[fx>0]=fx[fx>0]
  outside=np.argwhere((body!=cur)&(fx==0))
  Image.fromarray(fx).save(out/f'effect_{n:03}.png');a.rgba(fx).save(out/f'effect_{n:03}_rgba.png')
  effects.append({'ref':n,'body_ref':original,'effect_parts':semantic(extra['parts']),'effect_pixels':int((fx>0).sum()),'effect_sha256':sha(fx.tobytes()),'effect_clut':0,'current_independent_tile6_parts':semantic([p for p in cp['parts']if p['tile']==6]),'body_composition_prefix_matches':equal,'effect_overlay_reconstruction_exact':bool(np.array_equal(rebuilt,cur)),'current_visible_matching_effect_pixels':int(((fx>0)&(cur==fx)).sum()),'other_body_delta':[{'xy':[int(x-160),int(y-160)],'body':int(body[y,x]),'effect_frame':int(cur[y,x])}for y,x in outside],'note':'원래9효과54texel과 현재tile6원자료 동일. 현재73/74에는 몸체에 묻힌 효과와 별도권총차이가 있어 단순71/72+최상층효과 복사 금지.'})
 relations=[]
 for n in(67,68,71,72,73,74,93,94,217,218,220):
  a.layer(n);f=a.banks[0]['frames'][n];raw=a.raw[f['offset'],f['tile_count']].data
  layers={str(pb):sha(a.layer(n,pb)[0].tobytes())for pb in(0,5,6,7,8)}
  relations.append({'ref':n,'stream_offset':f['offset'],'tile_count':f['tile_count'],'raw_sha256':sha(raw),'layer_sha256':layers,'parts':{str(pb):semantic(composition_frame(a.c,pb,n)['parts'])for pb in(0,5,6,7,8)}})
 f93,f94=[q for q in relations if q['ref']in(93,94)]
 play=json.loads((ROOT/'work/sprite_consistency_20261105/playback/manifest.json').read_text('utf8'));anim=play['characters']['nana']['forms']['ultimate_before']['animations']; selected=[q for q in anim if any(s['frame_ref']in(*range(67,85),93,94,217,218,220)for s in q['steps'])]
 rows=[(f'nonfiring connector {n}',[('before',a.composite(n,15)[0]),('after',a.composite(n,0)[0])])for n in(93,94)]
 helper.grid(rows,out/'connectors.png',7)
 write(out/'manifest.json',{'parent_sha256':EXPECTED,'historical_effect_manifest':str(prior_path.relative_to(ROOT)),'historical_effect_manifest_sha256':digest(prior_path),'effects':effects,'relations':relations,'connector_93_94':{'raw_identical':f93['raw_sha256']==f94['raw_sha256'],'same_stream_offset':f93['stream_offset']==f94['stream_offset'],'body_layers_identical':f93['layer_sha256']==f94['layer_sha256'],'separate_pose_authorship_required':True},'animations':selected,'nova_policy':'73의 전체 몸을 복사하지 않는다. 이전 head mask와각217/218/220별좌표·효과를읽고새머리의미마스크로별도동기화한다. 아직새73미제작.'})
 print(json.dumps({'effects':[{'ref':x['ref'],'pixels':x['effect_pixels']}for x in effects],'connector_raw_equal':f93['raw_sha256']==f94['raw_sha256'],'connector_layers_equal':f93['layer_sha256']==f94['layer_sha256']}))
if __name__=='__main__':main()
