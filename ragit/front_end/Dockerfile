FROM python:3.10

WORKDIR /ragit

COPY ragit/front_end /ragit/front_end
COPY ragit/libs /ragit/libs

COPY requirements.txt /ragit
# RUN pip3 install --no-cache-dir -r /ragit/requirements.txt

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /ragit/requirements.txt

EXPOSE 13131/tcp
ENV PYTHONPATH="/"

CMD ["python3.10", "/ragit/front_end/app.py"]
