"""
Fix SVG paper figures:
1. Consistent HEIGHT across all, but variable WIDTH based on content
2. Larger font sizes for paper readability
3. Increased spacing to prevent text overlap
"""

import re
from pathlib import Path

# Paper figures directory
figures_dir = Path(r"plots\paper  figures")

# Chart area (viewBox) - Large enough to contain all elements without clipping
# This is the COORDINATE SYSTEM - keep consistent across all files
CHART_VIEWBOX = "0 0 1200 900"  # Much larger to prevent clipping and provide spacing

# SVG canvas sizes - HEIGHT consistent, WIDTH varies by content needs
CONSISTENT_HEIGHT = 900

# Files to fix (updated names)
svg_files = [
    "level_l1_fc_distribution_norm.svg",
    "level_l1_raw_norm.svg",
    "level_l1_zscore_fc_norm.svg"
]

# Width mapping: files with annotations (distribution, zscore) need more width
SVG_WIDTHS = {
    'level_l1_fc_distribution_norm.svg': 1600,  # Has FC annotations on side - needs extra width
    'level_l1_raw_norm.svg': 1200,              # No annotations
    'level_l1_zscore_fc_norm.svg': 1600         # Has z-score annotations - needs extra width
}

# New CSS with larger fonts for paper readability and increased spacing
new_style = """/* normalized */
text{font-size:22px !important;}
tspan{font-size:22px !important;}

/* Larger font sizing for paper readability */
text, tspan { font-size: 22px !important; }
.axis-title, .axis-label { font-size: 26px !important; font-weight: 700; }

/* VERY LARGE separation between ticks and axis titles to prevent overlap */
.x-axis-title { dominant-baseline: hanging; dy: 5.5em !important; }
.y-axis-title { text-anchor: end; dx: -4.5em !important; }

/* Increased tick labels spacing from axis to prevent overlap */
.axis .tick text { font-size: 22px !important; }
.x.axis .tick text { dy: 2.0em !important; }
.y.axis .tick text { dx: -1.8em !important; }

/* Ensure no clipping */
svg { 
    overflow: visible;
}
"""

print("=" * 70)
print("FIXING PAPER FIGURES SVG FILES")
print("=" * 70)

for svg_file in svg_files:
    svg_path = figures_dir / svg_file
    
    if not svg_path.exists():
        print(f"⚠️  Skipping {svg_file} (not found)")
        continue
    
    # Get appropriate width for this file
    svg_width = SVG_WIDTHS.get(svg_file, 1000)  # Default to 1000 if not specified
    
    # Read SVG
    with open(svg_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix width (varies by content)
    content = re.sub(
        r'width="[^"]*"',
        f'width="{svg_width}"',
        content,
        count=1
    )
    
    # Fix height (consistent across all)
    content = re.sub(
        r'height="[^"]*"',
        f'height="{CONSISTENT_HEIGHT}"',
        content,
        count=1
    )
    
    # Fix viewBox (chart area stays consistent)
    content = re.sub(
        r'viewBox="[^"]*"',
        f'viewBox="{CHART_VIEWBOX}"',
        content,
        count=1
    )
    
    # Replace style section
    # Find the last <style> tag (the one we control)
    style_pattern = r'<style>[^<]*</style>(?!.*<style>)'
    if re.search(style_pattern, content, re.DOTALL):
        content = re.sub(
            style_pattern,
            f'<style>{new_style}</style>',
            content,
            flags=re.DOTALL
        )
    else:
        # If no style tag, add one before </svg>
        content = content.replace('</svg>', f'<style>{new_style}</style></svg>')
    
    # Write back
    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed {svg_file}")
    print(f"   - SVG Width: {svg_width}px (content-specific)")
    print(f"   - SVG Height: {CONSISTENT_HEIGHT}px (consistent)")
    print(f"   - ViewBox: {CHART_VIEWBOX} (consistent coordinate system)")
    print(f"   - Larger fonts (22px base, 26px titles)")
    print(f"   - Increased spacing without clipping")

print("\n" + "=" * 70)
print("DONE! All SVG files standardized and spacing improved.")
print("=" * 70)
