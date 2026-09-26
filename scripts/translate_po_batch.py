import time
import polib
import translators as ts

def translate_po_file(filepath, target_lang):
    po = polib.pofile(filepath)
    # Include both completely untranslated entries and fuzzy entries
    entries_to_translate = [entry for entry in po if (not entry.msgstr or 'fuzzy' in entry.flags) and entry.msgid]
    total = len(entries_to_translate)
    print(f"[{target_lang}] Found {total} untranslated or fuzzy strings.")
    
    if total == 0:
        return
    
    for i, entry in enumerate(entries_to_translate):
        try:
            res = ts.translate_text(entry.msgid, from_language='pt', to_language=target_lang, translator='bing')
            entry.msgstr = res
            if 'fuzzy' in entry.flags:
                entry.flags.remove('fuzzy')
            print(f"[{target_lang}] {i+1}/{total}: '{entry.msgid}' -> '{res}'")
            time.sleep(0.1)
        except Exception as e:
            print(f"[{target_lang}] Error at {i} for '{entry.msgid}': {e}. Retrying with google...")
            try:
                res = ts.translate_text(entry.msgid, from_language='pt', to_language=target_lang, translator='google')
                entry.msgstr = res
                if 'fuzzy' in entry.flags:
                    entry.flags.remove('fuzzy')
                print(f"[{target_lang}] (google) {i+1}/{total}: '{entry.msgid}' -> '{res}'")
                time.sleep(0.5)
            except Exception as ex:
                print(f"  Failed fallback for '{entry.msgid}': {ex}")
        
        # Save progress every 25 translations
        if i % 25 == 0:
            po.save(filepath)
            
    po.save(filepath)
    print(f"[{target_lang}] Saved {filepath}\n")

if __name__ == '__main__':
    translate_po_file('translations/en/LC_MESSAGES/messages.po', 'en')
    translate_po_file('translations/es/LC_MESSAGES/messages.po', 'es')
