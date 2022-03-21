FROM python
WORKDIR /code
COPY . /code
RUN pip install -r requirements.txt
CMD python main.py

# docker build -t py_app .