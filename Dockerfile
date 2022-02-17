FROM python:3

WORKDIR /
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY which-ap.py .
COPY templates templates

CMD ["python", "-u", "which-ap.py"]
EXPOSE 5001
