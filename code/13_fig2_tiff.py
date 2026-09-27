"""Step 13. Convert Fig 2 (Stata PNG) to a PLOS-ready TIFF: 7.5 in wide at 300 dpi, LZW.

Input : output/figures/Fig2.png  (step 12)
Output: output/figures/Fig2.tif
"""
import os

from PIL import Image

from common import FIGURES_DIR

im = Image.open(os.path.join(FIGURES_DIR, "Fig2.png")).convert("RGB")
w = 2250
im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
im.save(os.path.join(FIGURES_DIR, "Fig2.tif"), compression="tiff_lzw", dpi=(300, 300))
print("Fig 2:", im.size, "->", FIGURES_DIR)
