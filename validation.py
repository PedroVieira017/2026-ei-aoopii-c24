import re
from collections import Counter


COMMON_WORDS = {
    "a",
    "o",
    "as",
    "os",
    "de",
    "do",
    "da",
    "dos",
    "das",
    "em",
    "e",
    "ou",
    "que",
    "para",
    "por",
    "com",
    "um",
    "uma",
    "no",
    "na",
    "nos",
    "nas",
}

FORBIDDEN_PT_BR_TERMS = {
    "equipe",
    "esporte",
    "midia",
    "m\u00eddia",
    "secao",
    "se\u00e7\u00e3o",
    "time",
    "usuario",
    "usu\u00e1rio",
    "voce",
    "voc\u00ea",
}

UNSUPPORTED_CLAIM_TERMS = {
    "assegura",
    "asseguram",
    "assegurar",
    "comprova",
    "comprovam",
    "comprovar",
    "garante",
    "garantem",
    "garantir",
}


def count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text, flags=re.UNICODE))


def count_sentences(text: str) -> int:
    sentences = re.split(r"[.!?]+(?:\s|$)", text.strip())
    return len([sentence for sentence in sentences if sentence.strip()])


def count_paragraphs(text: str) -> int:
    paragraphs = re.split(r"\n\s*\n", text.strip())
    return len([paragraph for paragraph in paragraphs if paragraph.strip()])


def find_repeated_phrases(text: str, phrase_size: int = 5) -> list[str]:
    words = re.findall(r"\b\w+\b", text.lower(), flags=re.UNICODE)
    phrases = Counter(
        tuple(words[index : index + phrase_size])
        for index in range(len(words) - phrase_size + 1)
    )

    repeated_phrases = []
    for phrase, count in phrases.most_common():
        if count < 2:
            continue
        if all(word in COMMON_WORDS for word in phrase):
            continue
        repeated_phrases.append(f"{' '.join(phrase)} ({count}x)")

    return repeated_phrases[:3]


def find_terms(text: str, terms: set[str]) -> list[str]:
    normalized_text = text.lower()
    found_terms = []

    for term in sorted(terms):
        pattern = rf"\b{re.escape(term.lower())}\b"
        if re.search(pattern, normalized_text, flags=re.UNICODE):
            found_terms.append(term)

    return found_terms


def has_markdown_markers(text: str) -> bool:
    return bool(re.search(r"(\*\*|__|^#{1,6}\s|^\s*[-*]\s+)", text, re.MULTILINE))


def get_newsletter_body(text: str) -> str:
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if len(lines) <= 1:
        return text
    return "\n".join(lines[1:])


def get_text_for_repetition_check(format_key: str, text: str) -> str:
    if format_key in {"blog", "newsletter"}:
        lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
        if len(lines) > 1:
            return "\n".join(lines[1:])
    return text


def get_tweet_lines(text: str) -> list[str]:
    return [line.strip() for line in text.strip().splitlines() if line.strip()]


def has_thread_numbering(lines: list[str]) -> bool:
    if not lines:
        return False

    expected_total = len(lines)
    for expected_number, line in enumerate(lines, start=1):
        match = re.match(r"^(\d+)/(\d+)\s+\S", line)
        if not match:
            return False

        number, total = (int(value) for value in match.groups())
        if number != expected_number or total != expected_total:
            return False

    return True


def build_validation_checks(format_key: str, text: str) -> dict:
    metric_text = get_newsletter_body(text) if format_key == "newsletter" else text
    word_count = count_words(metric_text)
    sentence_count = count_sentences(metric_text)
    paragraph_count = count_paragraphs(metric_text)
    repeated_phrases = find_repeated_phrases(
        get_text_for_repetition_check(format_key, text)
    )
    pt_br_terms = find_terms(text, FORBIDDEN_PT_BR_TERMS)
    unsupported_claim_terms = find_terms(text, UNSUPPORTED_CLAIM_TERMS)
    tweet_lines = get_tweet_lines(text) if format_key == "tweet_thread" else []
    long_tweets = [
        f"{index + 1} ({len(line)} caracteres)"
        for index, line in enumerate(tweet_lines)
        if len(line) > 280
    ]

    checks = [
        {
            "ok": not repeated_phrases,
            "message": (
                "Sem repeticoes obvias de frases."
                if not repeated_phrases
                else f"Possiveis repeticoes: {', '.join(repeated_phrases)}."
            ),
        },
        {
            "ok": not has_markdown_markers(text),
            "message": "Sem marcadores Markdown visiveis."
            if not has_markdown_markers(text)
            else "Foram encontrados marcadores Markdown visiveis no texto.",
        },
        {
            "ok": not pt_br_terms,
            "message": "Sem termos comuns de portugues do Brasil."
            if not pt_br_terms
            else f"Possiveis termos de portugues do Brasil: {', '.join(pt_br_terms)}.",
        },
        {
            "ok": not unsupported_claim_terms,
            "message": "Sem verbos fortes de garantia ou comprovacao."
            if not unsupported_claim_terms
            else f"Confirma se estes termos estao suportados pelos factos: {', '.join(unsupported_claim_terms)}.",
        },
    ]

    if format_key == "blog":
        checks.append(
            {
                "ok": word_count <= 700,
                "message": "Blog dentro de um tamanho medio."
                if word_count <= 700
                else "Blog possivelmente demasiado longo para o objetivo.",
            }
        )
    elif format_key == "linkedin":
        checks.extend(
            [
                {
                    "ok": 2 <= paragraph_count <= 4,
                    "message": "LinkedIn com 2 a 4 paragrafos."
                    if 2 <= paragraph_count <= 4
                    else "LinkedIn fora do intervalo recomendado de 2 a 4 paragrafos.",
                },
                {
                    "ok": word_count <= 180,
                    "message": "LinkedIn curto."
                    if word_count <= 180
                    else "LinkedIn possivelmente demasiado longo.",
                },
            ]
        )
    elif format_key == "tweet_thread":
        checks.extend(
            [
                {
                    "ok": 3 <= len(tweet_lines) <= 6,
                    "message": "Thread com 3 a 6 tweets."
                    if 3 <= len(tweet_lines) <= 6
                    else "Thread fora do intervalo recomendado de 3 a 6 tweets.",
                },
                {
                    "ok": not long_tweets,
                    "message": "Todos os tweets respeitam o limite de 280 caracteres."
                    if not long_tweets
                    else f"Tweets acima de 280 caracteres: {', '.join(long_tweets)}.",
                },
                {
                    "ok": has_thread_numbering(tweet_lines),
                    "message": "Thread numerada no formato 1/n."
                    if has_thread_numbering(tweet_lines)
                    else "Thread deve estar numerada no formato 1/n, 2/n, etc.",
                },
                {
                    "ok": word_count <= 220,
                    "message": "Thread curta e adequada ao formato."
                    if word_count <= 220
                    else "Thread possivelmente demasiado longa.",
                },
            ]
        )
    elif format_key == "newsletter":
        checks.extend(
            [
                {
                    "ok": word_count <= 60,
                    "message": "Newsletter com no maximo 60 palavras no corpo."
                    if word_count <= 60
                    else "Newsletter ultrapassa o limite recomendado de 60 palavras no corpo.",
                },
                {
                    "ok": sentence_count <= 2,
                    "message": "Newsletter com no maximo 2 frases."
                    if sentence_count <= 2
                    else "Newsletter ultrapassa o limite recomendado de 2 frases.",
                },
                {
                    "ok": paragraph_count == 1,
                    "message": "Newsletter com um unico paragrafo."
                    if paragraph_count == 1
                    else "Newsletter deve ficar num unico paragrafo.",
                },
            ]
        )

    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "paragraph_count": paragraph_count,
        "checks": checks,
    }


def newsletter_needs_repair(text: str) -> bool:
    newsletter_body = get_newsletter_body(text)
    return (
        count_words(newsletter_body) > 60
        or count_sentences(newsletter_body) > 2
        or count_paragraphs(newsletter_body) != 1
        or has_markdown_markers(text)
    )
