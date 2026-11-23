"""Exercise a deployed app with synthetic data, then delete the test documents."""
import argparse
import secrets
import uuid

import httpx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    args = parser.parse_args()
    base = args.url.rstrip("/")
    with httpx.Client(base_url=base, timeout=120) as owner, httpx.Client(base_url=base, timeout=120) as reader:
        def account(client, label):
            email = f"cloud-check-{label}-{uuid.uuid4().hex}@example.com"
            response = client.post("/api/v1/sessions/register", json={"email": email, "password": secrets.token_urlsafe(24)})
            assert response.status_code == 201, response.status_code
            client.headers.update({"X-CSRF-Token": response.json()["csrf_token"], "Origin": base})
            return email

        account(owner, "owner")
        reader_email = account(reader, "reader")
        collection = owner.post("/api/v1/collections", json={"name": "Synthetic deployment verification"}).json()
        content = b"# Resume\nMy name is Morgan Rivera.\nExample Labs | Data Engineer        Jan 2026 - Present\nPipelines process daily reports."
        upload = owner.post("/api/v1/documents", data={"collection_id": collection["id"]}, files={"file": ("synthetic-resume.md", content)})
        assert upload.status_code == 202, upload.status_code
        source = upload.json()
        try:
            for question, expected in [("what is his name", "Morgan Rivera."), ("what is his current company", "Example Labs.")]:
                response = owner.post("/api/v1/answers", json={"question": question, "document_id": source["document_id"]})
                assert response.status_code == 200, response.status_code
                result = response.json()
                assert result["answer"] == expected, result["status"]
                citation = result["citations"][0]["id"]
                assert owner.get("/api/v1/citations/" + citation).status_code == 200
                assert reader.get("/api/v1/citations/" + citation).status_code == 404
            original = "/api/v1/versions/" + source["version_id"] + "/original"
            assert owner.get(original).content == content
            assert reader.get(original).status_code == 404
            grant = owner.post("/api/v1/documents/" + source["document_id"] + "/grants", json={"email": reader_email})
            assert grant.status_code == 201
            assert reader.get(original).content == content
            assert owner.delete("/api/v1/documents/" + source["document_id"] + "/grants/" + grant.json()["user_id"]).status_code == 204
            assert reader.get(original).status_code == 404
            assert owner.post("/api/v1/versions/" + source["version_id"] + "/reindex").status_code == 202
            jobs = owner.get("/api/v1/jobs").json()["items"]
            assert all(job["status"] == "ready" for job in jobs)
            fallback = owner.post("/api/v1/answers", json={"question": "What do pipelines process?"}).json()
            assert fallback["status"] == "evidence_only"
            assert "not enabled" in fallback["answer"]
            print("PASS: registration, upload, indexing, name/company answers, citations, private original, sharing, revocation, reindex, honest no-AI fallback")
        finally:
            assert owner.delete("/api/v1/documents/" + source["document_id"]).status_code == 204
            assert owner.get(original).status_code == 404
            print("PASS: test document and original removed")


if __name__ == "__main__":
    main()
