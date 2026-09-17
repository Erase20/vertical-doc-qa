from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_assessment_upload_requires_code_and_version() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/documents",
            data={
                "domain": "assessment",
                "doc_type": "scale_manual",
                "audience": "clinician",
            },
            files={"file": ("demo.md", b"test content", "text/markdown")},
        )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "ASSESSMENT_VERSION_REQUIRED"
