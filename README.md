# SEPAQ Availability Scraper

Finding available [SEPAQ](https://www.sepaq.com/) camp sites can be cumbersome once the majority of sites are reserved. If you want to find out which site has availability and at which dates it involves many steps (clicks) checking each camp site individually. I quickly got annoyed of this and hacked together this scraper. Currently, this scraper helps finding available *Prêt-à-camper* (Ready-to-camp in English) camp sites in all SEPAQ parks.

There's two modes:

* retrieving camp sites and their availabilities
* parsing the availabilities and generating a simple HTML outut listing the available date ranges

## How to use

1. Clone this repo
2. `python3.8 -m venv --prompt 'scraper' .venv`
3. `source .venv/bin/activate`
4. `pip install --upgrade pip`
5. `pip install -r requirements/base.txt`
6. `python sepaq.py > result.html`
7. Open `result.html`

### Download availabilities

`python sepaq.py --download --dir path/to/download/to`

**Important:** Please call this only once to not overburden SEPAQ's servers.

**Note:** The filtering of the *availability* endpoint does not seem to be working so each call returns the full availability calendar (several years), i.e., in total almost 300 MB (!) might be downloaded.

### Output availabilities

`python sepaq.py --parse --dir path/downloaded/to > output.html`

The output is currently just printed to the console so it is written to `output.html`. Open this file with your browser of choice.

Optional parameters to limit:

* `--min-days`: only show availability of a minumum of `n` days
* `--min-date`: minimum date for availability to be considered
* `--max-date`: maximum date for availability to be considered

For example, you might want to try to find at least `4` nights between `2021-06-24` and `2021-07-31`:

`python sepaq.py --parse --dir path/of/data --min-days 4 --min-date 2021-06-24 --max-date 2021-07-31 > output.html`

## Ideas for future work

* add support for different camp site types
* build nice UI to visualize available camp sites and provide filter
* add more filtering options (like on the SEPAQ website)
* output directly to a file (using template engine?)

## Development

### Set up development environment

1. `python3.8 -m venv --prompt 'scraper' .venv`
2. `source .venv/bin/activate`
3. `pip install --upgrade pip`
4. `pip install -r requirements/development.txt`
