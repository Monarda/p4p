FROM python:3.8

WORKDIR /src/
COPY . /src/
RUN pip install -r requirements-latest.txt
RUN python -m pip install --upgrade build
RUN python -m build

RUN pip install dist/p4p-4.1.12-cp38-cp38-linux_x86_64.whl

CMD ["sleep", "infinity"]