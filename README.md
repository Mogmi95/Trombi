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

~~~~
# This line is only to create a new lang
$ pybabel init -i messages.pot -d trombi/translations -l [LANG]

# Extract the existing strings from the application
$ pybabel extract -F babel.cfg -o messages.pot .

# Updating the translation files with the new strings
$ pybabel update -i messages.pot -d trombi/translations

# Editing the translations (poedit is a cool tool for that)
$ poedit trombi/translations/[LANG]/LC_MESSAGES/messages.po

# Compile all the translations into an optimized file for production
$ pybabel compile -d trombi/translations
~~~~
