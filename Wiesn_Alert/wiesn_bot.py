import os
from time import sleep
from datetime import datetime
import telebot
from telebot.types import InlineKeyboardMarkup as ikm
from telebot.types import InlineKeyboardButton as ikb
from dotenv import load_dotenv
from Functions.file_handler import save_pickle, load_pickle
from Functions.wiesn_shared import (
    DAYTIMES, WEEKDAYS, DEFAULT_PREFS,
    build_message_for, chunk_message, format_prefs, format_rule, entry_matches_filter,
)

SUBSCRIBERS_FILE = '../Data/wiesn_alert_subscribers.pickle'
STATUS_FILE = '../Data/wiesn_alert_status.pickle'

# Wichtig: Dieser Bot muss den GLEICHEN Token benutzen wie deine
# telegram_bot_sendtext-Funktion in wiesn_alert.py -- sonst reden Bot und
# Scraper mit unterschiedlichen Telegram-Bots und die Abonnenten bekommen
# nichts von den Alerts mit.
load_dotenv()
bot_token = str(os.getenv('TELEGRAM_V1_WIESNBOT_TOKEN'))       # <- Namen ggf. anpassen
admin_chat_id = str(os.getenv('TELEGRAM_V1ET4NH_CHATID'))   # <- für /getUserCount, ggf. anpassen

bot = telebot.TeleBot(bot_token, parse_mode='Markdown')

dict_subscribers = load_pickle(SUBSCRIBERS_FILE)
if 'Error' in dict_subscribers:
    dict_subscribers = {}

# Nicht-persistenter Zwischenspeicher für Regeln, die gerade im Assistenten
# angelegt/bearbeitet werden (muss nicht überleben, wenn der Bot neu startet).
draft_rules = {}

welcome_message = """
Hi! Ich bin der Wiesn-Alert-Bot 🍺🎡

Ich benachrichtige dich, sobald sich bei den Zweitmarkt-Tischreservierungen auf oktoberfest-booking.com etwas ändert.

Du bekommst ab jetzt Alerts für ALLE Angebote. Mit /filter kannst du dir eigene Regeln bauen -- z. B. "Mo-Do nur abends unter 300€" UND zusätzlich "Fr-So ganztags, egal welcher Preis". Mit /stop kannst du alles wieder abbestellen.
"""

help_message = """
/start - Alerts abonnieren
/stop - Alerts abbestellen
/filter - Eigene Filter-Regeln verwalten
/alle - Alle aktuellen Angebote ungefiltert anzeigen
/status - Prüfen, ob der Scraper noch läuft
/latest - Aktuell zu deinen Filtern passende Angebote anzeigen
/help - Diese Übersicht anzeigen
"""

WEEKDAY_STEP_TEXT = "*Neue Regel (1/3): Wochentage*\nFür welche Tage soll diese Regel gelten? (nichts auswählen = alle Tage)"
DAYTIME_STEP_TEXT = "*Neue Regel (2/3): Tageszeiten*\nFür welche Tageszeiten? (nichts auswählen = ganztags)"
PRICE_STEP_TEXT = "*Neue Regel (3/3): Preislimit*\nOptional einen Maximalpreis setzen, oder direkt speichern."


def get_prefs(chat_id):
    """Holt die Präferenzen eines Nutzers, legt sie bei Bedarf neu an.
    Migriert auch ältere Datenformate (nur True/False, oder ein einzelner
    flacher Filter statt einer Regel-Liste)."""
    prefs = dict_subscribers.get(chat_id)

    if not isinstance(prefs, dict):
        was_active = bool(prefs) if prefs is not None else True
        prefs = dict(DEFAULT_PREFS)
        prefs['rules'] = []
        prefs['active'] = was_active
        dict_subscribers[chat_id] = prefs
        return prefs

    if 'rules' not in prefs:
        old_rule = {
            'weekdays': prefs.pop('weekdays', []) or [],
            'daytimes': prefs.pop('daytimes', []) or [],
            'max_price': prefs.pop('max_price', None),
        }
        has_filter = old_rule['weekdays'] or old_rule['daytimes'] or old_rule['max_price'] is not None
        prefs['rules'] = [old_rule] if has_filter else []
        dict_subscribers[chat_id] = prefs

    return prefs


def get_draft(chat_id):
    return draft_rules.setdefault(chat_id, {
        'weekdays': [], 'daytimes': [], 'max_price': None, 'edit_index': None,
    })


def rules_list_keyboard(prefs):
    kb = ikm()
    for i, rule in enumerate(prefs.get('rules') or []):
        kb.add(ikb(f"✏️ {i + 1}. {format_rule(rule)}", callback_data=f"rule_edit:{i}"))
        kb.add(ikb(f"🗑 Regel {i + 1} löschen", callback_data=f"rule_delete:{i}"))
    kb.add(ikb("➕ Neue Regel hinzufügen", callback_data="rule_new"))
    if prefs.get('rules'):
        kb.add(ikb("🔄 Alle Regeln löschen", callback_data="reset_filters"))
    return kb


def weekday_step_keyboard(draft):
    kb = ikm()
    for wd in WEEKDAYS:
        mark = "✅" if wd in draft['weekdays'] else "⬜️"
        kb.add(ikb(f"{mark} {wd}", callback_data=f"rule_toggle_weekday:{wd}"))
    kb.add(ikb("Weiter ➡️", callback_data="rule_step_daytime"))
    kb.add(ikb("❌ Abbrechen", callback_data="rule_cancel"))
    return kb


def daytime_step_keyboard(draft):
    kb = ikm()
    for dt in DAYTIMES:
        mark = "✅" if dt in draft['daytimes'] else "⬜️"
        kb.add(ikb(f"{mark} {dt}", callback_data=f"rule_toggle_daytime:{dt}"))
    kb.add(ikb("⬅️ Zurück", callback_data="rule_step_weekday"))
    kb.add(ikb("Weiter ➡️", callback_data="rule_step_price"))
    kb.add(ikb("❌ Abbrechen", callback_data="rule_cancel"))
    return kb


def price_step_keyboard(draft):
    kb = ikm()
    if draft['max_price'] is None:
        kb.add(ikb("💶 Preislimit eingeben", callback_data="rule_price_input"))
    else:
        kb.add(ikb(f"💶 Preislimit ändern (aktuell {draft['max_price']:.0f} €)", callback_data="rule_price_input"))
        kb.add(ikb("🚫 Preislimit entfernen", callback_data="rule_price_clear"))
    kb.add(ikb("⬅️ Zurück", callback_data="rule_step_daytime"))
    kb.add(ikb("✅ Regel speichern", callback_data="rule_save"))
    kb.add(ikb("❌ Abbrechen", callback_data="rule_cancel"))
    return kb


@bot.message_handler(commands=['start', 'home'])
def send_welcome(message):
    chat_id = str(message.chat.id)
    prefs = get_prefs(chat_id)
    prefs['active'] = True
    save_pickle(dict_subscribers, SUBSCRIBERS_FILE)
    bot.send_message(message.chat.id, welcome_message)


@bot.message_handler(commands=['stop'])
def stop_alert(message):
    chat_id = str(message.chat.id)
    if chat_id in dict_subscribers:
        get_prefs(chat_id)['active'] = False
        save_pickle(dict_subscribers, SUBSCRIBERS_FILE)
    bot.send_message(message.chat.id,
                      'Alerts gestoppt! Mit /start kannst du sie jederzeit wieder aktivieren '
                      '(deine Regeln bleiben gespeichert).')


@bot.message_handler(commands=['filter', 'einstellungen'])
def filter_cmd(message):
    chat_id = str(message.chat.id)
    prefs = get_prefs(chat_id)
    bot.send_message(message.chat.id, format_prefs(prefs), reply_markup=rules_list_keyboard(prefs))


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = str(call.message.chat.id)
    prefs = get_prefs(chat_id)
    action = call.data

    if action == "filter_menu":
        bot.edit_message_text(format_prefs(prefs), call.message.chat.id, call.message.message_id,
                               reply_markup=rules_list_keyboard(prefs), parse_mode='Markdown')

    elif action == "rule_new":
        draft_rules[chat_id] = {'weekdays': [], 'daytimes': [], 'max_price': None, 'edit_index': None}
        bot.edit_message_text(WEEKDAY_STEP_TEXT, call.message.chat.id, call.message.message_id,
                               reply_markup=weekday_step_keyboard(draft_rules[chat_id]), parse_mode='Markdown')

    elif action.startswith("rule_edit:"):
        idx = int(action.split(":", 1)[1])
        rule = prefs['rules'][idx]
        draft_rules[chat_id] = {
            'weekdays': list(rule['weekdays']), 'daytimes': list(rule['daytimes']),
            'max_price': rule['max_price'], 'edit_index': idx,
        }
        bot.edit_message_text(WEEKDAY_STEP_TEXT, call.message.chat.id, call.message.message_id,
                               reply_markup=weekday_step_keyboard(draft_rules[chat_id]), parse_mode='Markdown')

    elif action.startswith("rule_delete:"):
        idx = int(action.split(":", 1)[1])
        if 0 <= idx < len(prefs['rules']):
            prefs['rules'].pop(idx)
            save_pickle(dict_subscribers, SUBSCRIBERS_FILE)
        bot.edit_message_text(format_prefs(prefs), call.message.chat.id, call.message.message_id,
                               reply_markup=rules_list_keyboard(prefs), parse_mode='Markdown')

    elif action == "rule_step_weekday":
        draft = get_draft(chat_id)
        bot.edit_message_text(WEEKDAY_STEP_TEXT, call.message.chat.id, call.message.message_id,
                               reply_markup=weekday_step_keyboard(draft), parse_mode='Markdown')

    elif action.startswith("rule_toggle_weekday:"):
        wd = action.split(":", 1)[1]
        draft = get_draft(chat_id)
        if wd in draft['weekdays']:
            draft['weekdays'].remove(wd)
        else:
            draft['weekdays'].append(wd)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
                                       reply_markup=weekday_step_keyboard(draft))

    elif action == "rule_step_daytime":
        draft = get_draft(chat_id)
        bot.edit_message_text(DAYTIME_STEP_TEXT, call.message.chat.id, call.message.message_id,
                               reply_markup=daytime_step_keyboard(draft), parse_mode='Markdown')

    elif action.startswith("rule_toggle_daytime:"):
        dt = action.split(":", 1)[1]
        draft = get_draft(chat_id)
        if dt in draft['daytimes']:
            draft['daytimes'].remove(dt)
        else:
            draft['daytimes'].append(dt)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
                                       reply_markup=daytime_step_keyboard(draft))

    elif action == "rule_step_price":
        draft = get_draft(chat_id)
        bot.edit_message_text(PRICE_STEP_TEXT, call.message.chat.id, call.message.message_id,
                               reply_markup=price_step_keyboard(draft), parse_mode='Markdown')

    elif action == "rule_price_input":
        orig_chat_id = call.message.chat.id
        orig_message_id = call.message.message_id
        msg = bot.send_message(call.message.chat.id, "Bitte gib den maximalen Preis in Euro ein (z. B. 300):")
        bot.register_next_step_handler(msg, process_rule_price, chat_id, orig_chat_id, orig_message_id)

    elif action == "rule_price_clear":
        draft = get_draft(chat_id)
        draft['max_price'] = None
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
                                       reply_markup=price_step_keyboard(draft))

    elif action == "rule_save":
        draft = get_draft(chat_id)
        rule = {'weekdays': draft['weekdays'], 'daytimes': draft['daytimes'], 'max_price': draft['max_price']}
        rules = prefs.setdefault('rules', [])
        if draft['edit_index'] is not None and 0 <= draft['edit_index'] < len(rules):
            rules[draft['edit_index']] = rule
        else:
            rules.append(rule)
        save_pickle(dict_subscribers, SUBSCRIBERS_FILE)
        draft_rules.pop(chat_id, None)
        bot.edit_message_text("Regel gespeichert ✅\n\n" + format_prefs(prefs), call.message.chat.id,
                               call.message.message_id, reply_markup=rules_list_keyboard(prefs),
                               parse_mode='Markdown')

    elif action == "rule_cancel":
        draft_rules.pop(chat_id, None)
        bot.edit_message_text(format_prefs(prefs), call.message.chat.id, call.message.message_id,
                               reply_markup=rules_list_keyboard(prefs), parse_mode='Markdown')

    elif action == "reset_filters":
        prefs['rules'] = []
        save_pickle(dict_subscribers, SUBSCRIBERS_FILE)
        bot.edit_message_text("Alle Regeln gelöscht ✅\n\n" + format_prefs(prefs), call.message.chat.id,
                               call.message.message_id, reply_markup=rules_list_keyboard(prefs),
                               parse_mode='Markdown')

    bot.answer_callback_query(call.id)


def process_rule_price(message, chat_id, orig_chat_id, orig_message_id):
    try:
        price = float(message.text.replace('€', '').replace(',', '.').strip())
    except ValueError:
        bot.send_message(message.chat.id,
                          "Das war keine gültige Zahl. Ruf /filter nochmal auf und versuch's erneut.")
        return

    draft = get_draft(chat_id)
    draft['max_price'] = price

    try:
        bot.edit_message_reply_markup(orig_chat_id, orig_message_id, reply_markup=price_step_keyboard(draft))
    except Exception:
        pass  # Nachricht evtl. zu alt zum Editieren -- nicht schlimm, Preis ist trotzdem im Draft gesetzt

    bot.send_message(message.chat.id,
                      f"Preislimit auf {price:.0f} € gesetzt. Nicht vergessen: oben auf "
                      f"'✅ Regel speichern' tippen!")

def escape_markdown(text):
    """Verhindert, dass Sonderzeichen in Usernamen/Namen (z. B. Unterstriche)
    Telegrams Markdown-Parsing durcheinanderbringen und die Nachricht mit
    einem 400er ablehnen lassen."""
    for ch in ('_', '*', '`', '['):
        text = text.replace(ch, '\\' + ch)
    return text


@bot.message_handler(commands=['status'])
def status(message):
    status_data = load_pickle(STATUS_FILE)
    if 'Error' in status_data or 'last_run' not in status_data:
        bot.send_message(message.chat.id, "Noch kein Check gelaufen (oder Status-Datei nicht gefunden).")
        return

    last_run = status_data['last_run']
    entry_count = status_data.get('entry_count', 0)
    minutes_ago = int((datetime.now() - last_run).total_seconds() // 60)

    prefs = get_prefs(str(message.chat.id))
    matching = 0
    if 'data' in status_data:
        matching = sum(1 for e in status_data['data'].values() if entry_matches_filter(e, prefs))

    text = (
        f"*Wiesn-Alert Status*\n"
        f"Letzter Check: {last_run.strftime('%d.%m.%Y %H:%M:%S')} (vor {minutes_ago} Min.)\n"
        f"Angebote insgesamt: {entry_count}\n"
        f"Davon passend zu deinen Filtern: {matching}"
    )
    # SLEEP im Scraper ist 300s (5 Min) -- deutlich länger her ist verdächtig
    if minutes_ago > 15:
        text += "\n\n⚠️ Der letzte Check ist ungewöhnlich lange her - der Scraper könnte hängen oder abgestürzt sein."

    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['latest'])
def latest(message):
    status_data = load_pickle(STATUS_FILE)
    if 'Error' in status_data or 'data' not in status_data:
        bot.send_message(message.chat.id, "Aktuell sind keine Angebote bekannt.")
        return

    prefs = get_prefs(str(message.chat.id))
    personal_message = build_message_for(status_data['data'], prefs)

    if not personal_message:
        bot.send_message(message.chat.id, "Aktuell gibt es keine Angebote, die zu deinen Filtern passen.")
        return

    for chunk in chunk_message(personal_message):
        bot.send_message(message.chat.id, chunk, disable_web_page_preview=True)


@bot.message_handler(commands=['alle'])
def all_offers(message):
    status_data = load_pickle(STATUS_FILE)
    if 'Error' in status_data or 'data' not in status_data:
        bot.send_message(message.chat.id, "Aktuell sind keine Angebote bekannt.")
        return

    # Kein prefs-Argument = kein Filter, komplette Liste
    full_message = build_message_for(status_data['data'])

    if not full_message:
        bot.send_message(message.chat.id, "Aktuell gibt es keine Angebote.")
        return

    for chunk in chunk_message(full_message):
        bot.send_message(message.chat.id, chunk, disable_web_page_preview=True)

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.send_message(message.chat.id, help_message)


@bot.message_handler(commands=['getUserCount'])
def getuser(message):
    if str(message.chat.id) != admin_chat_id:
        bot.send_message(message.chat.id, "Error! You are not authorized to do that!")
        return

    active_ids = [cid for cid, p in dict_subscribers.items() if isinstance(p, dict) and p.get('active')]
    inactive_count = sum(1 for p in dict_subscribers.values() if isinstance(p, dict) and not p.get('active'))

    if not active_ids:
        bot.send_message(message.chat.id, f"Aktive Abonnenten: 0 (abgemeldet: {inactive_count})")
        return

    lines = [f"*Aktive Abonnenten:* {len(active_ids)} (abgemeldet: {inactive_count})", ""]
    for cid in active_ids:
        try:
            chat = bot.get_chat(cid)
            if chat.username:
                name = f"@{chat.username}"
            else:
                name = ' '.join(filter(None, [chat.first_name, chat.last_name])) or f"chat_id {cid}"
        except Exception:
            name = f"(nicht erreichbar, chat_id {cid})"

        rules = dict_subscribers[cid].get('rules') or []
        filter_info = f"{len(rules)} Regel(n)" if rules else "kein Filter"
        lines.append(f"• {escape_markdown(name)} — {filter_info}")

    text = "\n".join(lines)
    for chunk in chunk_message(text):
        bot.send_message(message.chat.id, chunk)


@bot.message_handler(func=lambda message: True)
def fallback(message):
    bot.send_message(message.chat.id, 'Das habe ich nicht verstanden. Nutze /help für alle verfügbaren Befehle.')


# Start Bot
print('Wiesn Bot Listener started..')
while True:
    try:
        print('Bot started..')
        bot.polling(none_stop=True)
    except Exception as e:
        print(f'Bot restart.. ({e})')
        sleep(5)