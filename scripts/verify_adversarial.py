"""Real generated-output checks, distinguishing quoted attacks from generated obedience."""
import argparse
import json
from pathlib import Path

from sqlalchemy import select

from knowdoc.answers import answer
from knowdoc.db import session
from knowdoc.models import Collection, Document, User
from knowdoc.providers import ProviderError


def main(email):
    dataset = json.loads(Path('evals/benchmark.json').read_text())
    rows = []
    with session() as db:
        user = db.scalar(select(User).where(User.email == email))
        corpus = db.scalar(select(Collection).where(Collection.owner_id == user.id, Collection.name.like('PostgreSQL%')))
        for case in dataset['cases']:
            if case['category'] not in {'unanswerable', 'prompt_injection'}:
                continue
            filters = {'collection_id': corpus.id}
            if case.get('document_filter'):
                document = db.scalar(select(Document).where(Document.owner_id == user.id, Document.title == case['document_filter']))
                filters = {'document_id': document.id}
            try:
                output = answer(db, user.id, case['question'], mode='generate', method='hybrid', **filters)
                generated = json.dumps({'answer': output['answer'], 'claims': output['claims']})
                rows.append({'case_id': case['id'], 'category': case['category'], 'output': output,
                             'no_forbidden_generated_text': not any(s in generated for s in case.get('forbidden_outputs', []))})
                print(case['id'], output['status'], flush=True)
            except ProviderError as exc:
                rows.append({'case_id': case['id'], 'category': case['category'], 'error': str(exc)})
    path = Path('artifacts/evaluations/adversarial-generated.json')
    path.write_text(json.dumps({'description': 'Actual local outputs. Forbidden generated strings exclude clearly identified source text; not human semantic grading.', 'cases': rows}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('email')
    main(parser.parse_args().email)
