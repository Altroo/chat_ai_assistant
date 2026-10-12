"""Backend-owned responses: planning cannot invent financial answers."""
CLARIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "reason": {"type": "string", "enum": ["missing_details", "ambiguous_metric", "unsupported"]},
        "language": {"type": "string", "enum": ["fr", "en"]},
    },
    "required": ["reason", "language"],
    "additionalProperties": False,
}
MESSAGES = {
    "fr": {
        "missing_details": "Précisez l’élément recherché ou la période concernée (avec l’année).",
        "ambiguous_metric": "Quel montant ou indicateur souhaitez-vous consulter, et pour quelle période (avec l’année) ?",
        "unsupported": "Cette demande n’est pas disponible dans l’assistant avec vos accès actuels. Je peux vous aider à retrouver des éléments autorisés ou à comprendre les procédures de cette application.",
    },
    "en": {
        "missing_details": "Please specify the record you mean or the relevant period (including the year).",
        "ambiguous_metric": "Which amount or measure would you like to see, and for what period (including the year)?",
        "unsupported": "This request is not available in the assistant with your current access. I can help find records you can access or explain this application’s documented workflows.",
    },

}


def clarification_message(reason, language):
    return MESSAGES[language][reason]


def message_language(text, interface_language='fr'):
    """Infer the current English/French message; UI language only breaks ties."""
    import re
    import unicodedata
    normalized=''.join(c for c in unicodedata.normalize('NFKD',text.casefold()) if not unicodedata.combining(c))
    words=set(re.findall(r"[a-z]+",normalized))
    english_signals={'how','what','where','which','explain','please','show','does','meaning','tell','find','search','could','would'}
    french_signals={'comment','quoi','quel','quelle','quels','explique','expliquez','affiche','affichez','signifie','ou','cherche','chercher','montre','montrez','trouve','pouvez'}
    english=4*len(words & english_signals)+len(words & {'the','an','about','creating','invoice','is','are','can','this','my','for'})
    french=4*len(words & french_signals)+len(words & {'le','la','les','une','des','du','champ','facture','est','sont','cette','mon','pour'})
    return 'en' if english>french or (english==french and interface_language=='en') else 'fr'


def missing_knowledge_message(text, interface_language='fr'):
    if message_language(text, interface_language)=='en':
        return 'I could not find an approved explanation for that question within your access. Please specify the page or workflow you mean.'
    return 'Je ne trouve pas de procédure vérifiée pour cette question parmi les informations accessibles. Précisez la page ou l’opération concernée.'
