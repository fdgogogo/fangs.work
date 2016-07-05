FROM ruby:2.3-alpine
RUN apk add --update \
  build-base \
  libxml2-dev \
  libxslt-dev \
  postgresql-dev \
  && rm -rf /var/cache/apk/*
VOLUME /srv/jekyll
ADD ./Gemfile /code/Gemfile
WORKDIR /code/
RUN bundle install

WORKDIR /srv/jekyll
CMD bundle install && jekyll build
