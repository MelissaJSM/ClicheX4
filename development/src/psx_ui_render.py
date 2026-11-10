"""Native indexed UI rendering with each part's real palette offset."""
from PIL import Image
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition


def render_static_rgba(texture, composition, palettes):
    _, size, bounds, _ = compose_static(texture, local_composition(composition))
    output = Image.new('RGBA', size)
    for part in composition['parts']:
        offset = part['clut']
        if offset not in palettes or len(palettes[offset]) != 16:
            raise ValueError('Missing native UI part palette')
        indices, ps, pb, _ = compose_static(texture, local_composition({**composition, 'parts': [part]}))
        colors = [(int(w&31)*255//31, int((w>>5)&31)*255//31, int((w>>10)&31)*255//31, 255 if i else 0)
                  for i,w in enumerate(palettes[offset])]
        picture = Image.frombytes('RGBA', ps, bytes(v for i in indices for v in colors[i]))
        output.alpha_composite(picture, (pb[0]-bounds[0], pb[1]-bounds[1]))
    return output, bounds
