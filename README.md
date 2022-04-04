You write it, and we deliver it.
================================

[![Build Status](https://travis-ci.org/ciudadanointeligente/write-it.png?branch=master)](https://travis-ci.org/ciudadanointeligente/write-it)
[![Coverage Status](https://coveralls.io/repos/ciudadanointeligente/write-it/badge.png?branch=master)](https://coveralls.io/r/ciudadanointeligente/write-it)
[![Code Health](https://landscape.io/github/ciudadanointeligente/write-it/master/landscape.png)](https://landscape.io/github/ciudadanointeligente/write-it/master)

Write-it is an application that aims to deliver messages to people whose contacts are to be private or the messages should be public, for example: members of congress.

Write-it is a layer on top of [popit](http://popit.mysociety.org) from where it takes the people and adds contacts. The way it delivers messages is using plugins for example: mailit. And this approach allows for future ways of delivering for example: twitter, whatsapp, fax or pager.

Future uses are in [congresoabierto](http://www.congresoabierto.cl) to replace the old "preguntales" (You can [check here](http://congresoabierto.cl/comunicaciones), to see how it used to work) feature, it was inspired by [writetothem](http://www.writetothem.com/).

Installation instructions for developers are below. If you'd like to integrate WriteIt with your civic tech application it's recommended that you use the [hosted version](http://writeit.ciudadanointeligente.org/en/) and read `INTEGRATION_GUIDE.md` in this directory for integration instructions.

Production deployment
=====================

Provide these environment variables:

| Key                   | Description
| ----------------------|----------------
| DATABASE_URL          | e.g `postgresql://user:password@hostname/dbname`
| DEFAULT_FROM_DOMAIN   | e.g. `writeinpublic.yourdomain.com`
| DJANGO_SECRET_KEY     | Must be secret
| DJANGO_ADMINS         | comma-separated list of name and email, e.g. `Bob:bob@example.com,Sally:sally@example.com`
| ELASTICSEARCH_INDEX   | e.g. `writeinpublic-prod`
| ELASTICSEARCH_URL     | e.g. `http://elasticsearch.host.com:9200/`
| EMAIL_HOST            |
| EMAIL_HOST_PASSWORD   |
| EMAIL_HOST_USER       |
| EMAIL_USE_TLS         | True if you provide the string `True`
| SENTRY_DSN            | Optional - provide the DSN to enable Sentry error logging
| SESSION_COOKIE_DOMAIN | start with dot to support subdomains e.g. `.writeinpublic.yourtdomain.com`
| TIME_ZONE             | Optional - e.g. `Africa/Johannesburg`

Run the django web service, the celery worker, and celery beat for scheduled tasks.


Handle incoming mail
--------------------

Incoming mail can be delivered using the `mailit` manage command `handeemail` or via HTTP POST webhook.


### Manage command

The handleemail command takes an email MIME object on standard input - call once per email. This can be used for example with the Exim .forward pipe transport.


### Sengrid inbound parse (raw) webhook

Configure the Inbound Parse webhook to POST to /mailit/inbound/sendgrid/raw/ on the central domain.

Make sure to select RAW format.

Handle message delivery logging web hooks
-----------------------------------------

Configure the sendgrid email event web hook to POST to `/mailreporter/`


Local development using docker-compose
======================================

This directory is mapped as a volume in the app. This can result in file permission errors like `EACCES: permission denied`. File permissions are generally based on UID integers and not usernames, so it doesn't matter what users are called, UIDs have to match or be mapped to the same numbers between the host and container.

We want to avoid running as root in production (even inside a container) and we want production to be as similar as possible to dev and test.

The easiest solution is to make this directory world-writable so that the container user can write to install/update stuff. Be aware of the security implications of this. e.g.

    sudo find . -type d -exec chmod 777 '{}' \;

Another good option is to specify the user ID to run as in the container. A persistent way to do that is by specifying `user: ${UID}:${GID}` in a `docker-compose.yml` file, perhaps used as an overlay, and specifying your host user's IDs in an environment file used by docker-compose, e.g. `.env`.

Install database schema

    docker-compose run --rm web ./manage.py migrate

Compile translations

    docker-compose run --rm web ./manage.py compilemessages

You can load some fixtures with:

    docker-compose run --rm web ./manage.py loaddata example_data.yaml

Then run the development server with:

    docker-compose up

And visit http://127.0.0.1.xip.io:8000 on your host machine to use WriteIt.

You can enable the [debug-toolbar](https://django-debug-toolbar.readthedocs.io/en/latest/) by setting `DJANGO_DEBUG_TOOLBAR=true`


### Background jobs

Background job processes are also run by docker-compose in development.

Background jobs are run by the Celery worker

    celery -A writeit worker

This handles syncing contact details from remote sources. If you
have created a new instance and the contacts do not seem to be syncing
it is probably because a celery worker is not running.

### Scheduled jobs

Scheduled jobs are queued for the worker by Celery beat

    celery -A writeit beat

This sends emails to recipients and periodically re-sync contacts from
remote sources.


Manual Installation (without docker-compose)
============================================

System Requirements
-------------------

 * [Elasticsearch](http://www.elasticsearch.org/)

 It's required if you want to play around seaching messages and answers, this part is optional.

 Your version of the Python `elasticsearch` package must match
 the version of Elasticsearch you have.  The `requirements.txt`
 file in this repository currently specifies
 `elasticsearch==1.6.0`, which will only work with Elasticsearch
 with a major version of 1. If you have a 0.x or 2.x version of
 Elasticsearch you will need to install a different version of
 the Python `elasticsearch` package. For more details on how to
 pick the right version to use, see:
 https://elasticsearch-py.readthedocs.io/en/master/#compatibility

 * [Urllib3](http://urllib3.readthedocs.org/en/latest/)

 * [libffi](https://sourceware.org/libffi/)

 In ubuntu you can do ```sudo apt-get install libffi-dev```

 * Libssl

 In ubuntu you can do ```sudo apt-get install libssl-dev```

 * GCC (G++) 4.3+ (used by python libsass package)

 In ubuntu you can do ```sudo apt-get install g++```

 * yui-compressor

 In ubuntu you can do ```sudo apt-get install yui-compressor```

Write-it is built using Django. You should install Django and its dependencies inside a virtualenv. We suggest you use [virtualenvwrapper](http://virtualenvwrapper.readthedocs.org/en/latest/) to create and manage virtualenvs, so if you don’t already have it, [go install it](http://virtualenvwrapper.readthedocs.org/en/latest/install.html#basic-installation), remembering in particular to add the required lines to your shell startup file.

With virtualenvwrapper installed, clone this repo, `cd` into it, and create a virtualenv:

    git clone git@github.com:ciudadanointeligente/write-it.git
    cd write-it
    mkvirtualenv writeit

Install the requirements:

    pip install -r requirements.txt

Set up the database, creating an admin user when prompted:

    ./manage.py syncdb && ./manage.py migrate

Compile all the available translations:

    ./manage.py compilemessages


Troubleshooting database migration
----------------------------------
There's a problem migrating and the problem looks like

	django.db.utils.OperationalError: no such table: tastypie_apikey

It can be fixed by running it twice.

Then run the server:

    ./manage.py runserver




Testing and Development
=======================

If you want to test without Elasticsearch
-----------------------------------------------------
Elasticsearch is optional and can be turned off by creating a new local_settings.py file ```vi writeit/local_settings.py``` with the following content


```
LOCAL_ELASTICSEARCH = False
```

Running tests
--------------

For testing you need to run ```./manage.py test nuntium contactos mailit instance```

Coverage Analysis
-----------------
For coverage analysis run ./coverage.sh

Logging in
--------------
At this point you probably have write-it running without any users. You could create a (super) user by running:

```
python manage.py createsuperuser
```

It will ask you the username and password (which you will need to repeat).

With that done you will be able to access '/accounts/login/'.

Updating Translations
---------------------

The following procedure should safely get new translations from
Transifex and push any new messages for translation back to
Transifex:

```
tx pull -a -f
```

Commit those changes, since Transifex has no history, and when
we push back to Transifex any removed translations will no
longer appear there:

```
git commit -m "Recording the latest translations from Transifex" -- locale
```

Extract all translation strings from the code, and update the
`.po` files so that any new strings for translation are added:


```
./manage.py makemessages -a --no-wrap
```

This will add fuzzily inferred translations to the `.po`
files, but they won't be added to Transifex when we upload
(since it doesn't support fuzzy translations) and later we'll
pull back from transifex to remove them.

Push any new strings to Transifex with:

```
tx push -s -t --skip
```

If you pull from Transifex again, that should remove the fuzzy
translations:

```
tx pull -a -f
```

Now you can commit the result:

```
git commit -m "Updated .po files from makemessages" -- locale
```

And run:

```
./manage.py compilemessages
```

API clients
===========

Write-it has been used mostly through its REST API for which there are a number of API clients.
The github repos and the status of the development are listed below:
- [writeit-rails](https://github.com/ciudadanointeligente/writeit-rails) ALPHA
- [writeit-django](https://github.com/ciudadanointeligente/writeit-django) ALPHA


There are instructions to install write-it in heroku
----------------------------------------------------
The instructions are in [the following link](deploying_to_heroku.md).