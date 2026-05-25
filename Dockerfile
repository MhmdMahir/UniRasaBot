FROM python:3.10

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 7860

CMD ["rasa", "run", "--enable-api", "--cors", "*", "--model", "models", "--port", "7860", "--host", "0.0.0.0"]