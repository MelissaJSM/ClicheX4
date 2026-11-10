"""동결 호버의 검증된 패커를 별도 노바 모듈로 만들며 원본은 보존한다."""
from pathlib import Path
D=Path(__file__).resolve().parent
def main():
 src=(D.parent/'ultimate_hover_repaint/pack_native.py').read_text('utf8')
 replacements={
 '새 호버50층을 원5사격공유스트림·고정은행에 저장하고 재독출한다.':'새 노바40층을 원6공유그룹·고정은행에 저장하고 재독출한다.',
 'comp,PBS,KEYS,REFS,PARENT,BEFORE':'comp,PBS,GROUPS,REFS,PARENT,BEFORE',
 'for key in KEYS:\n  ns=[key,key+1];':'for group in GROUPS:\n  ns=list(group);key=ns[0];',
 '[16]*10':'[16]*(len(ns)*5)',
 "'target_layers_exact':50":"'target_layers_exact':40",
 "default='targets_preview_v3'":"default='targets_preview_v1'",
 "default='packed_hover_candidate_v1'":"default='packed_nova_candidate_v1'",
 'Physical shot pair stream sharing':'Original physical stream group sharing',
 '새5몸체와 원발사표에 정합한 새5사격팔의 50층 후보. 원5공유stream/각32타일/은행경계·비대상 소유 보존. 실제 호버는 mask15이며 layer5는 하체다. 독립·MIPS·원순서·실기는 별도.':'새 준비213/215와돌진217을8참조40층으로 등록한 후보. 원6 raw그룹과타일수/은행경계/비대상보존.213..216 의상,217..220 본체/효과소유를분리. 독립·MIPS·원순서·실기는별도.'
 }
 for old,new in replacements.items():
  if old not in src:raise ValueError('Expected source text missing: '+old)
  src=src.replace(old,new)
 old="for i in range(0,len(REFS),2):helper.grid([(str(n),[('idle reference',b.composite(0,0)[0]),('old actual mask15',a.composite(n,15)[0]),('new actual mask15',b.composite(n,15)[0]),('new upper0 / incomplete',b.composite(n,0)[0])])for n in REFS[i:i+2]],out/f'readback_{i//2+1}.png',6)"
 new="for i in range(0,len(REFS),2):helper.grid([(str(n),[('idle reference',b.composite(0,0)[0]),('old mask15',a.composite(n,15)[0]),('new mask15',b.composite(n,15)[0]),('new acquired0'if n<217 else'technical base0',b.composite(n,0)[0])])for n in REFS[i:i+2]],out/f'readback_{i//2+1}.png',5 if i<4 else 4)"
 if old not in src:raise ValueError('Expected readback loop missing')
 src=src.replace(old,new);dst=D/'pack_native.py'
 if dst.exists():raise ValueError('Existing Nova packer')
 dst.write_text(src,'utf8');print(dst)
if __name__=='__main__':main()
