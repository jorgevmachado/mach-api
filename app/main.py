from http import HTTPStatus

from fastapi import FastAPI
from fastapi_pagination import add_pagination

from app.core.logging import configure_logging
from app.shared.schemas import Message

configure_logging()
app = FastAPI()

add_pagination(app)

@app.get('/', status_code=HTTPStatus.OK, response_model=Message)
def read_root():
    return {'message': 'Hello World!'}
