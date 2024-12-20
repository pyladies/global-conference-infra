> [!NOTE]
> This is a for from the EuroPython ProgramAPI. For more information
> check [their repository](https://github.com/EuroPython/programapi/)

# TODO

* Adapt the current state to accept the "Internal notes" field as the field
that will contain the YouTube link for each recorded proposal.

# PyLadiesCon programapi

This project downloads, processes, saves, and serves the static JSON files containing details of accepted speakers and submissions via an API.

Used by the EuroPython 2024 website and the Discord bot.

**What this project does step-by-step:**

1. Downloads the Pretalx speaker and submission data, and saves it as JSON files.
2. Transforms the JSON files into a format that is easier to work with and OK to serve publicly. This includes removing unnecessary/private fields, and adding new fields.
3. Serves the JSON files via an API.

## Installation

1. Clone the repository.
2. Install the dependency management tool: ``make deps/pre``
3. Install the dependencies: ``make deps/install``
4. Set up ``pre-commit``: ``make pre-commit``

## Configuration

You can change the event in the [``config.py``](src/config.py) file. It is set to ``pyladiescon-2024`` right now.

## Usage

- Run the whole process: ``make all``
- Run only the download process: ``make download``
- Run only the transformation process: ``make transform``

**Note:** Don't forget to set ``PRETALX_TOKEN`` in your ``.env`` file at the root of the project. And please don't make too many requests to the Pretalx API, it might get angry 🤪

## API

> [!WARNING]
> This is not implemented for PyLadiesCon

The API is served at ``https://programapi24.europython.eu/2024``. It has two endpoints (for now):

- ``/speakers.json``: Returns the list of confirmed speakers.
- ``/sessions.json``: Returns the list of confirmed sessions.

## Schema

See [this page](data/examples/README.md) for the explanations of the fields in the returned JSON files.
