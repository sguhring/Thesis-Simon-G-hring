import sys
from pptx import Presentation
from pptx.util import Emu

src = sys.argv[1]
prs = Presentation(src)
print(f"Slide size: {Emu(prs.slide_width).inches:.2f} x {Emu(prs.slide_height).inches:.2f} in, {len(prs.slides)} slides\n")
for i, s in enumerate(prs.slides, 1):
    print(f"=== Slide {i} (layout: {s.slide_layout.name}) ===")
    for sh in s.shapes:
        kind = sh.shape_type
        name = sh.name
        if sh.has_text_frame and sh.text_frame.text.strip():
            txt = sh.text_frame.text.strip().replace("\n", " | ")
            print(f"[{name}] {txt}")
        elif getattr(sh, "has_table", False) and sh.has_table:
            print(f"[{name}] TABLE:")
            for r in sh.table.rows:
                print("   " + " || ".join(c.text.strip() for c in r.cells))
        elif getattr(sh, "has_chart", False) and sh.has_chart:
            ch = sh.chart
            title = ch.chart_title.text_frame.text if ch.has_title else ""
            print(f"[{name}] CHART type={ch.chart_type} title='{title}'")
            try:
                for p in ch.plots:
                    cats = list(p.categories)
                    for ser in p.series:
                        print(f"   series '{ser.name}': cats={cats[:12]} vals={list(ser.values)[:12]}")
            except Exception as e:
                print("   (chart data unreadable)", e)
        elif kind == 13:
            print(f"[{name}] PICTURE")
        elif sh.shape_type == 6:  # group
            for sub in sh.shapes:
                if sub.has_text_frame and sub.text_frame.text.strip():
                    print(f"[{name}/{sub.name}] {sub.text_frame.text.strip().replace(chr(10),' | ')}")
    if s.has_notes_slide and s.notes_slide.notes_text_frame.text.strip():
        print(f"[EXISTING NOTES] {s.notes_slide.notes_text_frame.text.strip()}")
    print()
