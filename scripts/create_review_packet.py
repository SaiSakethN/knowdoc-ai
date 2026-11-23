import json
from pathlib import Path

source = Path('artifacts/generation-probes-v2.json')
if not source.exists():
    raise SystemExit('Run public-corpus generation probes first')
questions = ['Which index type does CREATE INDEX use by default?', 'Which index type is preferred for text search?']
rows = json.loads(source.read_text())
text = '# Actual output review worksheet\n\nReviewer: ______  Date: ______\n\nThese are real public-corpus diagnostic outputs, not independently reviewed labels. Assess each claim against the actual stored evidence.\n'
for question, output in zip(questions, rows, strict=True):
    text += f'\n## {question}\n\nStatus: {output["status"]}\n\nAnswer:\n\n{output["answer"]}\n'
    for claim in output['claims']:
        text += f'\nClaim: {claim["text"]}\n\nQuoted evidence:\n\n```text\n{claim["quote"]}\n```\n\nSupport: supported / partial / unsupported\n\nRationale: ______\n'
    text += '\nCorrectness: correct / partial / incorrect / abstention\n\nReviewer notes: ______\n'
destination = Path('artifacts/review-worksheet.md')
destination.write_text(text, encoding='utf-8')
print(f'Created {destination}; no review labels were filled automatically.')
