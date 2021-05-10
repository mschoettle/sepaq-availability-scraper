import datetime
import json
from collections import namedtuple
from itertools import groupby
from operator import itemgetter
from pathlib import Path
from typing import Any, Dict

import requests
from bs4 import BeautifulSoup

DateRange = namedtuple('DateRange', ['start', 'end'])

# can also be added to a session
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:78.0) Gecko/20100101 Firefox/78.0',
}

# session = requests.Session()
# session.headers.update({'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:78.0) Gecko/20100101 Firefox/78.0'})

# response = session.get('https://www.sepaq.com/en/reservation/camping/init?type=Pr%C3%AAt%20%C3%A0%20camper')

# # response = session.get('https://www.sepaq.com/en/reservation/carte/resultats')

# soup: BeautifulSoup = BeautifulSoup(response.content, 'lxml')

# camp_sites = soup.body.select('a.resultats-item.is-blue')

# print(camp_sites[0]['href'])

# url = 'https://www.sepaq.com' + camp_sites[0]['href']

# response = session.get(url)

# print(len(json.loads(response.content)))
# response = session.get('https://www.sepaq.com/en/reservation/camping/camping-des-voltigeurs/camping-des-voltigeurs/zone-2/site-211')

# response = session.get('https://www.sepaq.com/en/reservation/availabilities?year=2021')

# print(response.content)

# with Path('avail.json').open('w') as fd:
    # json.dump(json.loads(response.content), fd, indent=2)


def dl_availabilities(session: requests.Session, current_path: Path):
    response = session.get('https://www.sepaq.com/en/reservation/availabilities?year=2021')

    with current_path.joinpath('availabilities.json').open('wb') as fp:
        fp.write(response.content)


def extract_camp_sites(session: requests.Session, current_path: Path, url: str):
    current_path.mkdir(exist_ok=True)

    # print('requesting: ' + url)
    response = session.get(url)

    soup: BeautifulSoup = BeautifulSoup(response.content, 'lxml')

    links = soup.body.select('a.resultats-item.is-blue')

    data = {}

    for link in links:
        name = link.h4.text
        link_url = 'https://www.sepaq.com' + link['href']
        sub_path = current_path.joinpath(name)

        # print(f'Found: {name} ({link_url})')

        children = extract_camp_sites(session, sub_path, link_url)

        data[name] = {
            'url': link_url,
            'children': children,
        }

        if len(children) == 0:
            print('getting availabilities for: ' + name)
            dl_availabilities(session, sub_path)

    return data


def get_availabilities(data, min_date, max_date):
    pass


# see: https://stackoverflow.com/a/59777417
def consecutive_groups(iterable, ordering=lambda x: x):
    for k, g in groupby(enumerate(iterable), key=lambda x: x[0] - ordering(x[1])):
        yield map(itemgetter(1), g)


if __name__ == '__main__':
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:78.0) Gecko/20100101 Firefox/78.0'
    })

    # data = extract_camp_sites(
    #     session,
    #     Path('tmp/sepaq/'),
    #     'https://www.sepaq.com/en/reservation/camping/init?type=Pr%C3%AAt%20%C3%A0%20camper'
    # )

    # with Path('campsites.json').open('w') as fp:
    #     json.dump(data, fp, indent=2)

    with Path('campsites.json').open() as fp:
        campsites = json.load(fp)

    # for filepath in Path('tmp/sepaq').rglob('*,json'):
    filepaths = sorted(Path('tmp/sepaq').rglob('*.json'))

    last_park = None
    # optional
    last_sub_park = None
    last_camp_site = None

    for filepath in filepaths:
        # print(filepath.parts)
        parts = filepath.parts[2:]
        park = parts[0]
        sub_park = parts[-4] if len(parts) == 5 else None
        camp_site = parts[-3]
        spot = filepath.parent.name

        if last_park != park:
            url = campsites[park]['url']
            print(f'<h2><a href="{url}">{park}</a></h2>')

        camp_site_combined = camp_site

        if sub_park is not None:
            url = campsites[park]['children'][sub_park]['children'][camp_site]['url']
            camp_site_combined = f'{sub_park} / {camp_site}'
        else:
            url = campsites[park]['children'][camp_site]['url']

        if last_camp_site != camp_site:
            print(f'<h3><a href="{url}">{camp_site_combined}<a/></h3>')

        min_date = datetime.date(2021, 7, 1)
        max_date = datetime.date(2021, 8, 15)

        with filepath.open() as fp:
            data = json.load(fp)

            filtered_data = {}

            for entry in data:
                date_string = entry['dateAsStandardString']
                date = datetime.datetime.strptime(date_string, '%Y-%m-%d').date()

                if date >= min_date and date <= max_date:
                    if entry['availability']:

                        filtered_data[date] = {
                            'date': date,
                            'availability': True,
                            'price': entry['minimalNightPrice']
                        }

            print(f'<h4>{spot}</h4>')
            print('<ul>')

            for g in consecutive_groups(filtered_data, ordering=lambda x: x.toordinal()):
                group = list(g)

                if len(group) >= 2:
                    print(f'<li>{min(group)} to {max(group)}</li>')

            print('</ul>')

        last_park = park
        last_sub_park = sub_park
        last_camp_site = camp_site
