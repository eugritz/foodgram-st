FROM python:3.11-alpine
WORKDIR /app
COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn
COPY . .
CMD python manage.py migrate; gunicorn backend.wsgi --bind 0.0.0.0:8000
