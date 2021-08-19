FROM python:3

# upgrade pip
RUN pip3 install --upgrade pip setuptools wheel

# get curl for healthchecks
RUN apt-get install curl
#RUN apk add curl

# permissions and nonroot user for tightened security
#RUN adduser -D nonroot
RUN useradd -ms /bin/bash nonroot
RUN mkdir /home/app/ && chown -R nonroot:nonroot /home/app
RUN mkdir -p /var/log/flask-app && touch /var/log/flask-app/flask-app.err.log && touch /var/log/flask-app/flask-app.out.log
RUN chown -R nonroot:nonroot /var/log/flask-app
WORKDIR /home/app
USER nonroot

# copy all the files to the container
COPY --chown=nonroot:nonroot . .

# venv
ENV VIRTUAL_ENV=/home/app/venv

# python setup
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN export FLASK_APP=main.py
RUN pip3 install -r requirements.txt

# define the port number the container should expose
EXPOSE 8000

CMD ["python", "main.py"]