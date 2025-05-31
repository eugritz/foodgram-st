FROM python:3.11-alpine
WORKDIR /app
COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn
RUN apk add curl
COPY . .
CMD python manage.py collectstatic --noinput; \
    python manage.py migrate; \
    gunicorn backend.wsgi --bind 0.0.0.0:8000
