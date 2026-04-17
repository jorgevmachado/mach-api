import logging
import re
from http import HTTPStatus

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.core.context.request_context import request_id_ctx
from app.core.logging.middleware import logging_middleware


def get_logged_record(caplog, levelname, logger_name='app'):
    for record in caplog.records:
        if record.levelname == levelname and record.name == logger_name:
            return record
    return None


def test_logging_middleware_success(monkeypatch, caplog):
    app = FastAPI()

    @app.middleware('http')
    async def custom_logging_middleware(request: Request, call_next):
        return await logging_middleware(request, call_next)

    @app.get('/ok')
    async def ok():
        return {'msg': 'ok'}

    # Set up app logger to propagate to root so caplog can capture
    app_logger = logging.getLogger('app')
    app_logger.propagate = True

    client = TestClient(app)
    with caplog.at_level(logging.INFO, logger='app'):
        response = client.get('/ok')
    assert response.status_code == HTTPStatus.OK
    # Print all log records for debugging
    print('Captured log records:')
    for r in caplog.records:
        print(f'LOG: {r.levelname} {r.name} {r.getMessage()}')
    record = get_logged_record(caplog, 'INFO')
    assert record is not None
    assert 'completed in' in record.getMessage()
    assert record.request_id is not None
    assert record.method == 'GET'
    assert record.path == '/ok'
    assert record.status_code == HTTPStatus.OK
    assert isinstance(record.duration, int)


def test_logging_middleware_exception(monkeypatch, caplog):
    app = FastAPI()

    @app.middleware('http')
    async def custom_logging_middleware(request: Request, call_next):
        return await logging_middleware(request, call_next)

    @app.get('/fail')
    async def fail():
        raise ValueError('fail!')

    # Set up app logger to propagate to root so caplog can capture
    app_logger = logging.getLogger('app')
    app_logger.propagate = True

    client = TestClient(app)
    with caplog.at_level(logging.ERROR, logger='app'):
        with pytest.raises(ValueError, match='fail!'):
            client.get('/fail')
    print('Captured log records:')
    for r in caplog.records:
        print(f'LOG: {r.levelname} {r.name} {r.getMessage()}')
    record = get_logged_record(caplog, 'ERROR')
    assert record is not None
    assert 'failed in' in record.getMessage()
    assert record.request_id is not None
    assert record.method == 'GET'
    assert record.path == '/fail'
    assert record.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert isinstance(record.duration, int)


def test_request_id_ctx_set_in_middleware():
    app = FastAPI()
    request_ids = []

    @app.middleware('http')
    async def custom_logging_middleware(request: Request, call_next):
        await logging_middleware(request, call_next)
        request_ids.append(request_id_ctx.get())
        return JSONResponse({'ok': True})

    @app.get('/id')
    async def get_id():
        return {'msg': 'ok'}

    client = TestClient(app)
    client.get('/id')
    assert request_ids[0] is not None
    assert re.match(r'^[0-9a-f\-]{36}$', request_ids[0])
