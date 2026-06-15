#!/usr/bin/env bash
# exit on error
set -o errexit

echo "-----> Install dependencies"
python -m pip install pipenv
pipenv install --system

echo "-----> I'm post-compile hook"
cd ./tabbycat/

echo "-----> Running database migration"
python manage.py migrate --noinput

echo "-----> Running dynamic preferences checks"
python manage.py checkpreferences

echo "-----> Compiling JS translation catalogs from .mo files"
# Must run before `npm run build`, whose `cp-i18n` step copies the freshly
# generated locale/jsi18n/** catalogs into static/jsi18n. Without this, the
# served gettext catalogs are only ever as current as the committed
# locale/jsi18n files, so .po/.mo edits silently fail to reach the browser.
python manage.py compilejsi18n

echo "-----> Running static asset compilation"
npm install -g @vue/cli-service-global
npm install
npm run build

echo "-----> Running static files compilation"
python manage.py collectstatic --noinput

echo "-----> Post-compile done"
