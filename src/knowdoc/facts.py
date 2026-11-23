"""Conservative document-profile facts. Values always resolve to stored source spans."""
import re


def profile_intent(question: str) -> str | None:
    q = question.lower().strip(" ?.!\n")
    if re.search(r"\b(current|present)\s+(company|employer|organization)\b|\bwhere\s+(?:do|does|is)\s+(?:you|he|she|they|the candidate)\s+(?:currently\s+)?work", q):
        return "current_company"
    if re.search(r"\b(your|my|his|her|their|candidate'?s)\s+(full\s+)?name\b", q) or q in {"who am i", "who is the candidate"}:
        return "name"
    if re.search(r"\b(your|my|his|her|their|candidate'?s)\s+(current\s+|present\s+)?(role|job|position|job title)\b", q):
        return "current_role"
    return None


def profile_queries(intent: str) -> tuple[str, str]:
    if intent == "name":
        return '"my name" OR "self introduction"', "What is the full name of the person introducing themselves in this document?"
    return 'currently OR present OR "current role" OR "self introduction"', "What is this person's current employer and job title? Resume work experience employment dates Present."


def extract_profile_fact(question: str, passages: list[dict]) -> dict | None:
    intent = profile_intent(question)
    if not intent:
        return None
    matches = []
    for passage in passages:
        text = passage['text']
        if intent == 'name':
            match = re.search(r"\b[Mm]y\s+name\s+is\s+([A-Z][A-Za-z'’-]*(?:\s+[A-Z][A-Za-z'’-]*){0,5})\s*[.!]", text)
            if match:
                name = ' '.join(match[1].split())
                matches.append((name, passage, match[0]))
        else:
            # Use an explicit present-tense introduction. Never promote a previous role.
            title = re.search(r"\bI\s+am\s+(?:a|an)\s+([^.!\n]{3,90}?)(?=\s+(?:with|at|for)\b|[.!])", text)
            employer = re.search(r"\bCurrently,?\s+I\s+am\s+working\s+at\s+([^,\n.!]{2,90})", text, re.I)
            if employer and intent == 'current_company':
                matches.append((' '.join(employer[1].split()), passage, employer[0]))
            elif title and employer:
                role, company = ' '.join(title[1].split()), ' '.join(employer[1].split())
                # Evidence must contain both present-tense statements in this same stored chunk.
                start, end = min(title.start(), employer.start()), max(title.end(), employer.end())
                matches.append((f'{role} at {company}', passage, text[start:end]))
            # A resume's explicit date-to-Present employment line is evidence of
            # current employment. Never infer currentness from ordering alone.
            for line in text.splitlines():
                current = re.match(r"^\s*([^|\n]{2,100}?)\s*\|\s*(.{2,100}?)\s+((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\s*[-–—]\s*Present)\s*$", line, re.I)
                if current:
                    company, role = (' '.join(current[i].split()) for i in (1, 2))
                    value = company if intent == 'current_company' else f'{role} at {company}'
                    matches.append((value, passage, line))
    if not matches:
        return None
    unique = {value.casefold() for value, _, _ in matches}
    if len(unique) > 1:
        return {'status': 'clarification_required', 'answer': 'I found different profile details. Select the document or version you mean.',
                'claims': [], 'citations': [p for _, p, _ in matches[:4]]}
    value, source, quote = matches[0]
    return {'status': 'answered', 'answer': value + '.',
            'claims': [{'text': value + '.', 'citation_ids': [source['id']], 'quote': quote}],
            'citations': [source]}
