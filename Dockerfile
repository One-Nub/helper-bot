FROM python:3.11-slim

WORKDIR /bot 

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ src/

CMD ["python", "-u", "src/main.py"]
