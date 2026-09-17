from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_crisis_chat_uses_safety_response() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat/stream",
            json={
                "question": "我不想活了，应该怎么办？",
                "mode": "psychoeducation",
            },
        )

    assert response.status_code == 200
    assert "event: safety" in response.text
    assert '"level": "crisis"' in response.text
    assert "紧急服务" in response.text
    assert '"finish_reason": "crisis_support"' in response.text


async def test_invalid_domain_mode_is_rejected() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat/stream",
            json={"question": "测试", "mode": "unknown"},
        )

    assert response.status_code == 422
