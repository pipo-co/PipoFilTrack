FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

COPY . .

CMD [ "gunicorn", "-w 2", "-b 0.0.0.0:8000","main:app" ]