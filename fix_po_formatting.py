import polib
import re
from pathlib import Path

def fix_po_file(path):
    po = polib.pofile(path)
    for entry in po:
        if entry.msgid and entry.msgstr:
            # Fix %-based formatting
            if "%" in entry.msgid:
                specifiers = re.findall(r'%\([^)]+\)[sd]|%[sd]', entry.msgid)
                if any(s not in entry.msgstr for s in specifiers):
                    entry.msgstr = entry.msgid  # fallback

            # Fix {}-based formatting
            if "{" in entry.msgid and "}" in entry.msgid:
                braces = re.findall(r'\{[^}]+\}', entry.msgid)
                if any(b not in entry.msgstr for b in braces):
                    entry.msgstr = entry.msgid  # fallback

            # Newline consistency
            if entry.msgid.startswith("\n") and not entry.msgstr.startswith("\n"):
                entry.msgstr = "\n" + entry.msgstr
            if entry.msgid.endswith("\n") and not entry.msgstr.endswith("\n"):
                entry.msgstr = entry.msgstr + "\n"
            if not entry.msgid.startswith("\n") and entry.msgstr.startswith("\n"):
                entry.msgstr = entry.msgstr.lstrip("\n")
            if not entry.msgid.endswith("\n") and entry.msgstr.endswith("\n"):
                entry.msgstr = entry.msgstr.rstrip("\n")

    po.save(path)

base = Path("locale")
for lang in ['fa', 'tr', 'ru', 'fr', 'ar']:
    path = base / lang / "LC_MESSAGES" / "django.po"
    if path.exists():
        print(f"✅ Fixing: {path}")
        fix_po_file(path)
    else:
        print(f"⚠️  File not found: {path}")
