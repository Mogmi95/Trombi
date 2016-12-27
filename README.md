# Trombi

1. Clone the repository
2. Create a virtualenv (optional, but recommended)
3. Install pip dependencies ($ pip install -r requirements.txt)
4. Copy "config-example.py" as "config.py" and edit it with your configuration
4. Run $ python main.py
5. Open 127.0.0.1:5000 in your navigator
6. ???
7. Profit

# Translations

$ pybabel init -i messages.pot -d trombi/translations -l [LANG]
$ pybabel extract -F babel.cfg -o messages.pot .
$ pybabel update -i messages.pot -d trombi/translations
$ poedit trombi/translations/[LANG]/LC_MESSAGES/messages.po
$ pybabel compile -d trombi/translations
