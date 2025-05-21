import polib
from deep_translator import GoogleTranslator
import os

LANGUAGES = ['fa', 'tr', 'ru', 'fr', 'ar']  # You can add/remove language codes here

def translate_po(lang):
    path = f"locale/{lang}/LC_MESSAGES/django.po"
    print(f"Translating {path}...")

    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    po = polib.pofile(path)

    translator = GoogleTranslator(source='en', target=lang)

    count = 0
    for i, entry in enumerate(po):
        if not entry.translated() and entry.msgid.strip():
            try:
                translated = translator.translate(entry.msgid)
                entry.msgstr = translated or ""
                count += 1
            except Exception as e:
                print(f"Error translating '{entry.msgid}': {e}")
        
        # Safety: ensure msgstr is not None
        if entry.msgstr is None:
            entry.msgstr = ""

        if i % 50 == 0:
            print(f"Translated {i}/{len(po)} entries...")

    po.save(path)
    print(f"Done. {count} entries translated in {lang}.\n")

for lang in LANGUAGES:
    translate_po(lang)
