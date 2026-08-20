# Keynote production seq library (kong-bot)

**Project:** `/Users/bumsuklee/git/kong-bot` (not sky)  
**FS required** for xy from coordmap. Prefer `click_label`.  
**Sig refresh:** if screen/win/FS signature ≠ coordmap header → dump rewrite map before xy.

| name | when | do-not |
|------|------|--------|
| seq_fs.txt | enter FS once | never click exit-fullscreen |
| seq_close.txt | quit Keynote Don't Save | Terminal/Grok |
| seq_save.txt | save | invent save-as name |
| seq_newdoc.txt | new from chooser | recipe 4-guess coords |
| seq_add_slide.txt | add slide | |
| seq_shape.txt | insert shape | |
| seq_text_in_shape.txt | type in selected shape | |
| seq_align_num.txt | W/H/X/Y numeric | |
| seq_fill_hex.txt | fill color HEX | |
| seq_textcolor_hex.txt | text color HEX | |
| seq_object_list.txt | object list toggle | hard-fail if label missing |
| seq_deselect.txt | escape | |
| seq_delete.txt | backspace delete | |

Coordmap: `docs/appkb/keynote-coordmap.md` · `protocol/ar/verify_213/coordmap.json` (44 rows).
