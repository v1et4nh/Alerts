import re

PENDING_TEXT = "Ein Käufer befindet sich derzeit im Kaufprozess für diese Reservierung"
PENDING_MSG = f'_{PENDING_TEXT}_\n'

DAYTIMES = ['Vormittag', 'Mittag', 'Nachmittag', 'Abend']
WEEKDAYS = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']

DEFAULT_RULE = {
    'weekdays': [],      # leer = alle Wochentage
    'daytimes': [],      # leer = alle Tageszeiten
    'max_price': None,   # None = kein Limit
}

DEFAULT_PREFS = {
    'active': True,
    'rules': [],           # Liste von Regeln (DEFAULT_RULE-Form). Leer = kein Filter, alles passt.
}

TELEGRAM_MAX_LEN = 4096


def clean_text(text):
    """Mehrfache Whitespaces/Zeilenumbrüche zu einem einzigen Leerzeichen zusammenfassen."""
    return re.sub(r'\s+', ' ', text).strip()


def parse_price(price_str):
    """Wandelt einen deutschen Preis-String wie '€\xa01.059,90' in eine float-Zahl um.
    Gibt None zurück, wenn der String nicht geparst werden kann."""
    if not price_str:
        return None
    cleaned = price_str.replace('€', '').replace('\xa0', '').strip()
    cleaned = cleaned.replace('.', '').replace(',', '.')
    try:
        return float(cleaned)
    except ValueError:
        return None


def format_entry(e):
    lines = [f"[**{e['tent']}**]({e['tent_url']})"]
    lines.append(f"{e.get('date', '')} | {e.get('daytime', '')} | {e.get('time_range', '')}")
    lines.append(f"{e.get('persons', '')} | {e.get('tables', '')}")
    for label, price in e['items']:
        lines.append(f" - {label}" + (f": {price}" if price else ""))
    lines.append(f"---\nSumme: {e['total']}")
    return "\n".join(lines)


def entry_key(entry):
    """Stabiler Schlüssel für ein Angebot über mehrere Checks hinweg.

    Bewusst NICHT die Reservierungs-'id', da die bei einem laufenden
    Kaufprozess aus dem HTML verschwinden kann (Button wird deaktiviert).
    Ein Wechsel verfügbar <-> pending desselben Tisches zählt dadurch NICHT
    als neuer Tisch."""
    return (
        entry.get('tent', ''),
        entry.get('date', ''),
        entry.get('daytime', ''),
        entry.get('time_range', ''),
        entry.get('persons', ''),
        entry.get('tables', ''),
        entry.get('total', ''),
    )


def rule_matches(entry, rule):
    """Prüft, ob ein Angebot zu EINER einzelnen Regel passt (UND-Verknüpfung
    der in der Regel gesetzten Bedingungen)."""
    max_price = rule.get('max_price')
    if max_price is not None:
        price = parse_price(entry.get('total', ''))
        if price is not None and price > max_price:
            return False

    weekdays = rule.get('weekdays')
    if weekdays:
        weekday = entry.get('date', '').split(',')[0].strip()
        if weekday not in weekdays:
            return False

    daytimes = rule.get('daytimes')
    if daytimes:
        if entry.get('daytime') not in daytimes:
            return False

    return True


def entry_matches_filter(entry, prefs):
    """Ein Angebot passt, wenn der Nutzer KEINE Regeln definiert hat (= alles
    erlaubt), oder wenn es zu MINDESTENS EINER seiner Regeln passt (ODER
    zwischen den Regeln, UND innerhalb einer Regel)."""
    if not prefs:
        return True
    rules = prefs.get('rules')
    if not rules:
        return True
    return any(rule_matches(entry, rule) for rule in rules)


def build_message_for(data, prefs=None):
    """Baut die Telegram-Nachricht für ein data-Dict (wie von get_data()) auf,
    optional gefiltert nach individuellen Nutzer-Präferenzen."""
    message = ''
    for i in sorted(data):
        entry = data[i]
        if not entry_matches_filter(entry, prefs):
            continue
        if entry.get('pending'):
            message += PENDING_MSG
        message += format_entry(entry) + '\n\n'
    return message


def chunk_message(text, max_len=TELEGRAM_MAX_LEN):
    """Teilt einen Text an Eintragsgrenzen (doppelter Zeilenumbruch) in Stücke
    unter max_len Zeichen auf, statt Telegrams 4096-Zeichen-Limit pro Nachricht
    zu überschreiten (führt sonst zu 'Bad Request: message is too long')."""
    if len(text) <= max_len:
        return [text] if text else []

    chunks = []
    current = ''
    for block in text.split('\n\n'):
        candidate = f"{current}{block}\n\n"
        if len(candidate) > max_len:
            if current:
                chunks.append(current)
            if len(block) > max_len:
                for i in range(0, len(block), max_len):
                    chunks.append(block[i:i + max_len])
                current = ''
            else:
                current = f"{block}\n\n"
        else:
            current = candidate
    if current:
        chunks.append(current)

    return chunks


def format_rule(rule):
    weekdays = ', '.join(rule['weekdays']) if rule.get('weekdays') else 'alle Tage'
    daytimes = ', '.join(rule['daytimes']) if rule.get('daytimes') else 'ganztags'
    price = f"max. {rule['max_price']:.0f} €" if rule.get('max_price') is not None else 'kein Preislimit'
    return f"{weekdays} | {daytimes} | {price}"


def format_prefs(prefs):
    """Menschlich lesbare Zusammenfassung aller Filter-Regeln eines Nutzers."""
    rules = prefs.get('rules') or []
    if not rules:
        return "*Deine Filter:*\nKeine Regeln gesetzt – du bekommst alle Angebote."
    lines = ["*Deine Filter-Regeln* (ein Angebot reicht, wenn's zu einer davon passt):"]
    for i, rule in enumerate(rules, 1):
        lines.append(f"{i}. {format_rule(rule)}")
    return "\n".join(lines)