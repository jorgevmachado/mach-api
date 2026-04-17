FROM python:3.12-slim
ENV POETRY_VIRTUALENVS_CREATE=false

WORKDIR app/
COPY . .

RUN pip install poetry \
&& poetry config installer.max-workers 10 \
&& poetry install --no-interaction --no-ansi --without dev \
&& chmod +x entrypoint.sh

EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "--host", "0.0.0.0", "fast_zero.app:app"]