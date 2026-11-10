"""검토된 공통 화풍 지시와 페이지별 관절 위치를 분리해 프롬프트를 만든다."""
from pathlib import Path
H=Path(__file__).resolve().parent/'ladder_detail_inputs01'
original=(H/'page01_prompt.txt').read_text('utf8');before=original.split('Column 1 (game143):')[0];after=original[original.index('Top-row clothing from'):]
for n in(2,3):
 text=before+(H/f'page{n:02}_pose_spec.txt').read_text('utf8')+'\n'+after
 if n==3:text=text.replace('1536x1024','1024x1024').replace('three columns by two rows','two columns by two rows').replace('exact six placements','exact four placements')
 (H/f'page{n:02}_prompt.txt').write_text(text,'utf8')
print('2 prompts prepared; no generation')
