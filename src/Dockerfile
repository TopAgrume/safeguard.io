FROM python:3.10.14-slim

WORKDIR /app

COPY ./requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

CMD ["python3", "react_chatbot.py"]