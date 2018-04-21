# Trombi

This project is a light tool to help people recognise their colleagues when your company is getting bigger.

## Features

* List of all persons in the company
* Display only the new persons
* An organigram of the teams
* A little game to learn names of your colleagues
* A calendar with the birthdays and arrival dates of everyone
* Some spaces to display information for the users
* Links aggregator
* Reports on a person profile if an information is incorrect (only visible by the admin)
* Admin interface

## Screenshots

![Screenshot1](https://raw.githubusercontent.com/Mogmi95/Trombi/master/screenshots/trombi_screen.png)
![Screenshot1](https://raw.githubusercontent.com/Mogmi95/Trombi/master/screenshots/trombi_screen_2.png)
![Screenshot1](https://raw.githubusercontent.com/Mogmi95/Trombi/master/screenshots/trombi_screen_3.png)

# Installation

This project is using Flask and Python 2.7.

1. Clone the repository
2. Create a virtualenv (optional, but recommended)
3. Install pip dependencies ($ pip install -r requirements.txt)
4. Copy "config-example.py" as "config.py" and edit it with your configuration
4. Run $ python main.py
5. Open 127.0.0.1:5000 in your navigator
6. Access 127.0.0.1:5000/admin in your navigator to access the admin page (use the credentials from your `config.py` file.
7. Create persons manually or upload a CSV file in the Database section. The CSV format is given in `data/example-persons.csv`

I'm still actively working on this project, don't hesitate to comment or ask for some useful features :).

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
