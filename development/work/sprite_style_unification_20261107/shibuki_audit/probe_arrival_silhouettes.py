"""현재 광선의 몸체 합성 근거와 원래 외곽 보존 가능성을 조사한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page
from src.psx_player import composition_frame,decode_stream
from src.psx_sprite_batch import canvas_from_parts
from native_pose_pack import sha,need,write

def parts(a,n,ids):
 f=a.banks[0]['frames'][n];raw=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data;cp=composition_frame(a.c,0,n)
 return canvas_from_parts(raw,f['tile_count'],{**cp,'parts':[p for i,p in enumerate(cp['parts'])if i in ids]},(384,384),(160,160))
def over(bg,fg):r=bg.copy();r[fg>0]=fg[fg>0];return r
def main():
 data=(H/'prepared_victory_ladder01/PL00_U.ARC').read_bytes();need(sha(data)=='02f092d7b0ed67ce1174fd30250b86f73c81b42dbfa08c8c3ca06fc638b89acf','Source changed');a=Archive(data);out=H/'arrival_remaining01/silhouettes';need(not out.exists(),'Output exists');out.mkdir()
 oldbody=parts(a,131,range(16,24));ring=parts(a,131,range(16));need(np.array_equal(over(ring,oldbody),a.layer(131)[0]),'131 composition does not match')
 body140=parts(a,140,[0,1,2,3,4,5,6,9]);sparks140=parts(a,140,[7,8]);need(np.array_equal(over(body140,sparks140),a.layer(140)[0]),'140 decomposition mismatch')
 a133=a.layer(133)[0];a134=a.layer(134)[0];bg129=a.layer(129)[0];expected134=over(bg129,np.where(a133>0,np.where(a133==15,5,9),0).astype(np.uint8))
 oldsource=ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/original.arc';original=Archive(oldsource.read_bytes())
 historical=json.loads((ROOT/'work/ver_buki_riko/shibuki_art/remaining_v1/production14/art.json').read_text('utf8'));fx=np.array(historical['effect_index_mapping'],np.uint8)
 bg=original.layer(130)[0];bg[np.isin(bg,[5,8])]=14;bg=fx[bg]
 old133=np.array(Image.open(ROOT/'work/ver_buki_riko/shibuki_art/remaining_v1/production14/frame_133.png'));historicalbody=np.zeros((384,384),np.uint8);historicalbody[80:240,80:240]=old133
 expected130=over(bg,np.where(oldbody>0,9,0).astype(np.uint8));actual130=a.layer(130)[0]
 rows=dict(old131_body_equals_historical133_alpha=bool(np.array_equal(oldbody>0,historicalbody>0)),old131_body_equals_current133_alpha=bool(np.array_equal(oldbody>0,a133>0)),body131_pixels=int(np.count_nonzero(oldbody)),body140_equals_idle0_alpha=bool(np.array_equal(body140>0,a.layer(0)[0]>0)),body140_to_idle_alpha_changes=int(np.count_nonzero((body140>0)!=(a.layer(0)[0]>0))),frame134_exact_current133_bright_over129=bool(np.array_equal(expected134,a134)),frame134_difference=int(np.count_nonzero(expected134!=a134)),frame130_reconstruction_mismatch=int(np.count_nonzero(expected130!=actual130)),frame130_mismatch_outside_old_body=int(np.count_nonzero((expected130!=actual130)&(oldbody==0))),historical_original_arc_sha256=sha(oldsource.read_bytes()),current_source_sha256=sha(data))
 for name,q in [('131_old_body',oldbody),('131_ring',ring),('140_body',body140),('140_sparks',sparks140),('130_background',bg),('134_background',bg129)]:Image.fromarray(q).save(out/f'{name}_indices.png')
 page([('130 current',a.composite(130,0)[0]),('130 background',a.rgba(bg)),('131 body',a.rgba(oldbody)),('133 current',a.composite(133,0)[0]),('140 body',a.rgba(body140)),('current idle0',a.composite(0,0)[0])],a.composite(0,0)[0],out/'comparison.png',cols=3,scale=4)
 write(out/'proof.json',rows);print(json.dumps(rows))
if __name__=='__main__':main()
