"""Role-specific local Korean font masks; no palette, game-file or BIN writes.

Font files stay in the local Windows installation and are not packaged. The
caller owns native placement, palette quantization and atlas/cache allocation.
"""
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


@dataclass(frozen=True)
class FontProfile:
    filename: str
    face_index: int
    size: int
    slant: float = 0.0
    weight: int | None = None
    binary: bool = False
    description: str = ''


PROFILES = {
    'dialogue': FontProfile('gulim.ttc', 0, 12, binary=True,
                            description='Accepted dialogue; unchanged 12px 1bpp form'),
    'dialogue_graphic': FontProfile('H2GPRM.TTF', 0, 12, binary=True,
                                    description='Optional angular HY Graphic 12px dialogue; not automatically selected'),
    'menu': FontProfile('NotoSansKR-VF.ttf', 0, 12, .10, 600,
                        description='Generic menu; light italic; private 16x16 tiles with 12px advance'),
    'loading': FontProfile('H2GTRE.TTF', 0, 12, .25,
                           description='Bold italic loading and stage captions'),
    'title': FontProfile('H2GTRE.TTF', 0, 12, .20,
                         description='Bold italic main menu and medium emphasis'),
    'display': FontProfile('H2HDRM.TTF', 0, 22, .17,
                           description='Large headings; set slant=0 for upright boss names'),
}


def font_path(profile):
    spec = PROFILES[profile]
    path = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts' / spec.filename
    if not path.is_file():
        raise FileNotFoundError(f'Required local font is missing: {profile}: {path}')
    return path


@lru_cache(maxsize=128)
def _font(profile, size):
    spec = PROFILES[profile]
    face = ImageFont.truetype(str(font_path(profile)), size, index=spec.face_index)
    if spec.weight is not None:
        axes = face.get_variation_axes()
        if len(axes) != 1 or not axes[0]['minimum'] <= spec.weight <= axes[0]['maximum']:
            raise ValueError('Unexpected local variable-font weight axis')
        face.set_variation_by_axes([spec.weight])
    return face


def _fit(mask, max_size, binary):
    if max_size is None:
        return mask
    mw, mh = max_size
    if not isinstance(mw, int) or not isinstance(mh, int) or min(mw, mh) < 1:
        raise ValueError('Invalid mask size limit')
    size = (min(mask.width, mw), min(mask.height, mh))
    if size != mask.size:
        # A one-pixel metric overflow must be compressed, never cropped.
        mask = mask.resize(size, Image.Resampling.NEAREST if binary else Image.Resampling.BOX)
    return mask


def render_mask(text, profile, size=None, *, slant=None, binary=None, max_size=None):
    """Return a tight grayscale L mask (0..255) at native pixel resolution.

    Dialogue profiles retain direct monochrome rasterization and return only
    0/255. Other profiles retain native grayscale coverage for the caller to
    map to its actual CLUT. Slant shifts whole raster rows without resampling.
    This function never adds a shadow or changes palette indices.
    """
    if profile not in PROFILES:
        raise ValueError(f'Unknown typography profile: {profile}')
    if not isinstance(text, str) or not text or '\n' in text or '\r' in text:
        raise ValueError('A nonempty single line is required')
    spec = PROFILES[profile]
    size = spec.size if size is None else size
    if not isinstance(size, int) or not 1 <= size <= 128:
        raise ValueError('Font size must be between 1 and 128 pixels')
    slope = spec.slant if slant is None else slant
    if not 0 <= slope <= .5:
        raise ValueError('Unsupported font slant')
    mono = spec.binary if binary is None else binary
    face = _font(profile, size)
    box = face.getbbox(text)
    mask = Image.new('1' if mono else 'L', (max(1, box[2] - box[0]), max(1, box[3] - box[1])))
    ImageDraw.Draw(mask).text((-box[0], -box[1]), text, font=face, fill=1 if mono else 255)
    mask = mask.convert('L')
    bounds = mask.getbbox()
    if bounds:
        mask = mask.crop(bounds)
    if slope and bounds:
        skewed = Image.new('L', (mask.width + math.ceil(slope * (mask.height - 1)), mask.height))
        for row in range(mask.height):
            offset = round((mask.height - 1 - row) * slope)
            skewed.paste(mask.crop((0, row, mask.width, row + 1)), (offset, row))
        mask = skewed.crop(skewed.getbbox())
    return _fit(mask, max_size, mono)


def render_glyph_mask(char, profile='menu', size=None):
    """Prepare one native cache/menu glyph without silent clipping.

    At 12px menu size, ink is capped at 12x13. A caller's +1px drop shadow
    therefore occupies at most 13x14; placing it at tile y=2 fits 16x16.
    Native advance remains 12 and is controlled by existing part coordinates.
    The dialogue option is 12x12 binary and never adds a shadow.
    """
    if len(char) != 1 or char.isspace():
        raise ValueError('A single visible character is required')
    spec = PROFILES.get(profile)
    if spec is None:
        raise ValueError(f'Unknown typography profile: {profile}')
    actual_size = spec.size if size is None else size
    return render_mask(char, profile, actual_size,
                       max_size=(actual_size, actual_size if spec.binary else actual_size + 1))


def profile_metadata(profile):
    spec = PROFILES[profile]
    path = font_path(profile)
    return {'profile': profile, 'font_path': str(path), 'face_index': spec.face_index,
            'weight': spec.weight, 'default_size': spec.size, 'slant': spec.slant,
            'binary': spec.binary, 'family': list(_font(profile, spec.size).getname()),
            'font_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'description': spec.description,
            'font_file_copied_or_distributed': False, 'external_service_used': False,
            'distribution_authorized': False, 'font_redistribution_license_reviewed': False}


def profile_manifest():
    """Serializable provenance for local generated-mask proposal reports."""
    return {'profiles': {name: profile_metadata(name) for name in PROFILES},
            'mask_mode': 'L', 'coverage_range': [0, 255],
            'coordinates_and_palette_owned_by_caller': True,
            'menu_glyph_preparation': 'render_glyph_mask caps ink at 12x13 before a caller adds its 1px shadow',
            'local_preview_and_authorized_local_game_modification_only': True,
            'font_files_packaged': False, 'distribution_authorized': False}
