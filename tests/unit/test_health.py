from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from api.routes.health import health_check


@pytest.mark.unit
@pytest.mark.asyncio
@patch("redis.from_url")
async def test_health_check_all_healthy(mock_from_url: MagicMock) -> None:
    # Mock database to be healthy
    mock_db = AsyncMock()
    mock_db.execute.return_value = None

    # Mock Redis to be healthy
    mock_redis = MagicMock()
    mock_redis.ping.return_value = True
    mock_from_url.return_value = mock_redis

    # Call the health check endpoint
    response = await health_check(db=mock_db)

    assert response["status"] == "healthy"
    assert response["dependencies"]["postgres"] == "healthy"
    assert response["dependencies"]["redis"] == "healthy"
    mock_from_url.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
@patch("redis.from_url")
async def test_health_check_redis_unhealthy(mock_from_url: MagicMock) -> None:
    # Mock database to be healthy
    mock_db = AsyncMock()
    mock_db.execute.return_value = None

    # Mock Redis to raise an exception on ping
    mock_redis = MagicMock()
    mock_redis.ping.side_effect = Exception("Connection refused")
    mock_from_url.return_value = mock_redis

    # Call the health check endpoint
    with pytest.raises(HTTPException) as exc_info:
        await health_check(db=mock_db)

    assert exc_info.value.status_code == 503
    detail = exc_info.value.detail
    assert isinstance(detail, dict)
    assert detail["status"] == "unhealthy"
    assert detail["dependencies"]["postgres"] == "healthy"
    assert detail["dependencies"]["redis"] == "unhealthy"
