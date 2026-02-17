FROM python:3.9.22-bookworm

ENV PYTHONUNBUFFERED 1

COPY pkglist /tmp/
RUN apt-get update \
  && apt-get install -y $(cat /tmp/pkglist) \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# Copy, then install requirements before copying rest for a requirements cache layer.
COPY requirements.txt patch_packages.py /tmp/
RUN cd /tmp \
    && pip install --upgrade pip "setuptools<71" wheel \
    && pip install -r requirements.txt \
    && python /tmp/patch_packages.py

COPY . /app

WORKDIR /app

RUN DATABASE_URL=sqlite:///tmp/dummy.db \
    ELASTICSEARCH_URL=http://localhost:9200 \
    ELASTICSEARCH_INDEX=dummy \
    python manage.py compilemessages

RUN addgroup --system django \
    && adduser --system --ingroup django django \
    && mkdir -p /var/celerybeat /var/coverage /app/attachments \
    && chown -R django:django /var /app
USER django


EXPOSE 5000
CMD /app/bin/start.sh