"""Exercise real local API, worker, storage and citation boundaries using a synthetic account."""
import argparse
import json
import secrets
import time
from pathlib import Path

import httpx


def main(base_url, output):
    report = {"base_url": base_url, "checks": {}}
    with httpx.Client(base_url=base_url, timeout=15) as client:
        ready = client.get('/api/v1/health/ready')
        ready.raise_for_status()
        report['checks']['database_ready'] = ready.json()
        page = client.get('/')
        page.raise_for_status()
        assert 'KnowDoc AI' in page.text
        report['checks']['built_web_served'] = True
        account = client.post('/api/v1/sessions/register', json={
            'email': f'smoke-{secrets.token_hex(8)}@example.com', 'password': secrets.token_urlsafe(24)})
        account.raise_for_status()
        client.headers['X-CSRF-Token'] = account.json()['csrf_token']
        collection = client.post('/api/v1/collections', json={'name': 'Disposable smoke verification'})
        collection.raise_for_status()
        text = b'# Smoke indexing\nGIN indexes support full text search in this original verification fixture.'
        upload = client.post('/api/v1/documents', data={'collection_id': collection.json()['id'], 'label': 'smoke-v1'},
                             files={'file': ('smoke.md', text, 'text/markdown')})
        upload.raise_for_status()
        version_id, document_id = upload.json()['version_id'], upload.json()['document_id']
        for _ in range(60):
            versions = client.get(f'/api/v1/documents/{document_id}/versions').json()['items']
            if versions[0]['status'] == 'ready':
                break
            if versions[0]['status'] == 'failed':
                raise RuntimeError('smoke_ingestion_failed')
            time.sleep(1)
        else:
            raise RuntimeError('smoke_ingestion_timeout')
        report['checks']['real_embedding_ingestion'] = True
        result = client.post('/api/v1/answers', json={'question': 'GIN indexes text search', 'method': 'keyword', 'mode': 'evidence', 'document_id': document_id})
        result.raise_for_status()
        assert result.json()['status'] == 'evidence_only'
        citation_id = result.json()['citations'][0]['id']
        resolved = client.get(f'/api/v1/citations/{citation_id}')
        resolved.raise_for_status()
        assert resolved.json()['version'] == 'smoke-v1'
        assert resolved.json()['text'] == text.decode()
        original = client.get(f'/api/v1/versions/{version_id}/original')
        assert original.content == text
        report['checks']['answer_citation_and_original'] = True
        deleted = client.delete(f'/api/v1/documents/{document_id}')
        assert deleted.status_code == 204
        assert client.get(f'/api/v1/citations/{citation_id}').status_code == 404
        report['checks']['delete_revokes_citation'] = True
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    parser.add_argument('--output', default='artifacts/smoke.json')
    args = parser.parse_args()
    main(args.base_url, args.output)
