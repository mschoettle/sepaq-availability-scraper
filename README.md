# SEPAQ Availability Scraper

Finding available [SEPAQ](https://www.sepaq.com/) camp sites is cumbersome once the majority of sites are reserved. This scraper helps finding available camp sites (currently *Prêt-à-camper* (Ready-to-camp in English)) in all SEPAQ parks.

All camp sites with availabilities are retrieved and then the availability data for each park is downloaded. The availabilities are then parsed and a simple HTML report is created with camp sites and their availability.

## How to use

1. Clone this repo
2. `python3.8 -m venv --prompt 'scraper' .venv`
3. `source .venv/bin/activate`
4. `pip install --upgrade pip`
5. `pip install -r requirements/base.txt`
6. `python sepaq.py > result.html`
7. Open `result.html`

**Note:** The filtering of the *availability* endpoint does not seem to be working so each call returns the full availability calendar (several years), i.e., in total over 200 MB might be downloaded. Please don't call this too often to not overburden SEPAQ's servers.

## Set up development environment

1. `python3.8 -m venv --prompt 'scraper' .venv`
2. `source .venv/bin/activate`
3. `pip install --upgrade pip`
4. `pip install -r requirements/development.txt`
