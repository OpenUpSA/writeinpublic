FROM python:2.7

ENV PYTHONUNBUFFERED 1

COPY pkglist /tmp/
RUN sed -i 's/deb.debian.org/archive.debian.org/g' /etc/apt/sources.list \
  && sed -i 's|security.debian.org|archive.debian.org|g' /etc/apt/sources.list \
  && sed -i '/stretch-updates/d' /etc/apt/sources.list \
  && apt-get update \
  && apt-get install -y $(cat /tmp/pkglist) \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# Copy, then install requirements before copying rest for a requirements cache layer.
COPY requirements.txt /tmp/
RUN cd /tmp \
    && pip install -r requirements.txt

COPY . /app

WORKDIR /app

RUN python manage.py compilemessages

RUN addgroup --system django \
    && adduser --system --ingroup django django \
    && mkdir -p /var/celerybeat /var/coverage /app/attachments \
    && chown -R django:django /var /app
USER django


EXPOSE 5000
CMD /app/bin/start.sh