FROM registry.access.redhat.com/ubi9/python-311

WORKDIR /bot 

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ src/

CMD ["python", "-u", "src/main.py"]
