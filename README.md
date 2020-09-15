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

This project is using Python 2 and Flask. It is still compatible with Python 2.7, but python2 is going to be deprecated 2020, January 1st.

## Init

1. Clone the repository
2. Create a virtualenv `$ python3 -m venv venv`
3. Enter the virtualenv `$ source ./venv/bin/activate`
4. Install pip dependencies `(venv)$ pip install -r requirements.txt`
5. Copy "config-example.py" as "config.py" and edit it with your configuration
6. Configurate your project `(venv)$ export FLASK_APP=run.py`
7. Run `flask run`
8. Open 127.0.0.1:5000 in your navigator
9. Access 127.0.0.1:5000/admin in your navigator to access the admin page (use the credentials from your `config.py` file.
10. Enjoy!

I'm still actively working on this project, don't hesitate to comment or ask for some useful features :).

# API

If activated, an API is available to access data from the trombi. It follows a simple REST structure and doesn't require any authentication. The return format is JSON.

## Persons

Information about the persons.

* **URL**

`/api/persons/<login>`

* **Methods**

`[GET]`

* **Parameters**

|Parameter|Required|Value|Description|
|---|---|---|---|
|login|No|string|Request information for only one person|

**Success response**

* **Code:** 200 <br />

**Error response**

* **Code:** 404 <br /> The requested login doesn't exist

**Example response**

```json
[
    {
        "arrival": 1395270000,
        "surname": "O'Neil",
        "name": "Jack",
        "team_id": 2,
        "email": "oneil@sg1.com",
        "job": "Colonel",
        "birthday": 0,
        "login": "joneil",
        "id": 2,
        "picture": "/photo/joneil"
    },
    {
        "arrival": 1395270000,
        "surname": "Carter",
        "name": "Samantha",
        "team_id": 2,
        "email": "sam@sg1.com",
        "job": "Major",
        "birthday": 0,
        "login": "scarter",
        "id": 3,
        "picture": "/photo/scarter"
    },
    {
        "arrival": 1395270000,
        "surname": "",
        "name": "Teal'c",
        "team_id": 2,
        "email": "tealc@sg1.com",
        "job": "Jaffa",
        "birthday": 0,
        "login": "tealc",
        "id": 4,
        "picture": "/photo/tealc",
    }
]
```


## Teams

Information about the teams.

* **URL**

`/api/teams/<team_id>`

* **Methods**

`[GET]`

* **Parameters**

|Parameter|Required|Value|Description|
|---|---|---|---|
|team_id|No|integer|Request information for only one team|

**Success response**

* **Code:** 200 <br />

**Error response**

* **Code:** 404 <br /> The requested team doesn't exist

**Example response**

```json
[
    {
        "persons": ["ghammond"],
        "id": 1,
        "name": "SGC"
    },
    {
        "persons": [
            "joneil",
            "scarter",
            "tealc",
            "djackson",
            "jquinn"
        ],
        "higher_teaml_id": 1,
        "id": 2,
        "name": "SG1"
    }
]
```

## Links

Information about the links.

* **URL**

`/api/links/`

* **Methods**

`[GET]`

* **Parameters**

|Parameter|Required|Value|Description|
|---|---|---|---|
|-|-|-|-|

**Success response**

* **Code:** 200 <br />

**Example response**

```json
[
    {
        "url": "https://github.com/Mogmi95/Trombi",
        "description": "Github page of the Trombi project",
        "image_url": "https://dyw7ncnq1en5l.cloudfront.net/optim/news/75/75755/-c-github.jpg",
        "id": 1,
        "title": "Trombi on Github"
    }
]
```

# Translations

The translation section is still available, but it has not been heavily updated, since english is fine for most projects. I hope to propose a new translation later in the future.

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
