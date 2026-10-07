FROM python:3.12

RUN apt-get update && apt-get install -y build-essential git curl vim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt
RUN pip install pytest black mypy ipython

EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
