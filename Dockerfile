FROM python:3.11

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN rm requirements.txt

WORKDIR /app/src

COPY src/main.py /app/src/main.py
COPY src/util_funcs.py /app/src/util_funcs.py

EXPOSE 8000

CMD ["python", "/app/src/main.py"]
