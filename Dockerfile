FROM alpine:3.5

ENTRYPOINT ["python", "-m", "shortner"]
EXPOSE 8080
ENV FLASK_APP=/shortner/app.py

RUN LAYER=build \
  && apk add -U python py-pip \
  && pip install Flask redis \
  && rm -rf /var/cache/apk/* \
  && rm -rf ~/.cache/pip

ADD ./shortner /shortner
