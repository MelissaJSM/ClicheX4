"""새 승리206 후폼의 손목 연결만 builtin 편집할 입력을 복사한다."""
from pathlib import Path
import sys,json,shutil
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def main():
 d=H/'ultimate_victory206_arm01';need(not d.exists(),'Fresh local input');d.mkdir()
 s=H/'ultimate_victory_inputs01/page02';p=s/'generated.png';need(sha(p.read_bytes())=='32077bec52897fdc43a1dbc25ec1c332513ad633f2be124d0234901873b2087e','New source changed')
 shutil.copyfile(p,d/'edit_target.png');shutil.copyfile(s/'accepted_ultimate_style.png',d/'accepted_ultimate_style.png')
 prompt='''Precise local edit of Image1, a transparent1536x1024 pixel sprite sheet with four768x512 cells. Modify ONLY the raised bare arm of the BOTTOM LEFT sprite206. Image2 is a costume/skin reference. Keep the other three sprites and every other part of bottom-left206 exactly unchanged, including hair, sunglasses, eyes, head silhouette, torso/swimsuit, opposite low fist, thighs, sandals, feet and position. Do not rescale or recenter anything.
The bottom-left character must have exactly TWO hands total: the small low fist at its left chest and the single high fist immediately beside the right side of its head. The current bare forearm directly below the high fist has an extra fist-like bulge and dark break that makes the wrist look disconnected. Redraw only that bare wrist/forearm connection so the EXISTING high fist joins one continuous anatomically coherent bent arm. Preserve the high fist's current endpoint and its shape/height; match the upper-left206 jacket pose's same shoulder, elbow and wrist positions, simply without the sleeve. The forearm should narrow naturally into the wrist, with restrained skin highlight/shadow clusters, not a second hand or a detached cuff. Keep the arm in front of the same hair region with a clear silhouette, and keep the small elbow bend. No arm stretching, no extra fingers/hands, no recolored hair as skin and no jacket sleeve on this bare arm.
Keep clean console pixel clusters, moderate outlines, and actual transparent background. No glow, haze, labels, new accessories or any modifications outside the bottom-left raised arm. Preserve the fixed canvas and margins.
'''
 (d/'prompt.txt').write_text(prompt,'utf8');write(d/'input.json',{'refs':[206,207],'source_layout':json.loads((s/'input.json').read_text('utf8'))['source_layout'],'source':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())},'edit_scope':'after206의 올린 한 팔 손목/전완 연결만 국소 교정. 나머지 새 원화 전체 보호.','original_game_art_sent':False,'files':{p.name:sha(p.read_bytes())for p in d.iterdir()if p.is_file()}});print(d)
if __name__=='__main__':main()
