FROM python:3.12.5

WORKDIR /Mini-Golf-master
COPY . /Mini-Golf-master

RUN pip3 install --no-cache-dir -r Backend/requirements.txt

EXPOSE 8000

CMD ["python3", "Backend/app.py"]
