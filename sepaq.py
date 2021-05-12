import argparse
import datetime
import json
from collections import namedtuple
from itertools import groupby
from operator import itemgetter
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DateRange = namedtuple('DateRange', ['start', 'end'])

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:78.0) Gecko/20100101 Firefox/78.0',
}


def dl_availabilities(session: requests.Session, current_path: Path):
    # year query param does not seem to work to filter by year
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


# see: https://stackoverflow.com/a/59777417
def consecutive_groups(iterable, ordering=lambda x: x):
    for k, g in groupby(enumerate(iterable), key=lambda x: x[0] - ordering(x[1])):
        yield map(itemgetter(1), g)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--download',
        action='store_true',
        help='retrieve campsites from SEPAQ (IMPORTANT: expensive, do this only once!)',
    )
    parser.add_argument('--parse', action='store_true', help='parse availabilities and output a report')
    parser.add_argument('--dir', type=Path, help='directory where data should be stored to/read from', required=True)

    optional = parser.add_argument_group('optional arguments for parse option')
    optional.add_argument(
        '--min-days',
        dest='min_days',
        default=2,
        type=int,
        help='the number of minimum consecutive days to find availability for, default: 2',
    )
    optional.add_argument(
        '--min-date',
        dest='min_date',
        default=datetime.date.today(),
        type=datetime.date.fromisoformat,
        help='the minimum date in ISO format (YYYY-MM-DD), default: today',
    )
    optional.add_argument(
        '--max-date',
        dest='max_date',
        default=datetime.date.today() + datetime.timedelta(weeks=24),
        type=datetime.date.fromisoformat,
        help='the maximum date (inclusive) in ISO format (YYYY-MM-DD), default: 24 weeks (~6 months) from now',
    )

    args = parser.parse_args()

    if not args.download and not args.parse:
        parser.error('at least one of --download and --parse is required')

    campsites_file = args.dir.joinpath('campsites.json')
    min_days = args.min_days
    min_date = args.min_date
    max_date = args.max_date

    if args.download:
        # need to use a session across all requests due to heavy cookie use
        session = requests.Session()
        # fake user agent
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:88.0) Gecko/20100101 Firefox/88.0'
        })

        data = extract_camp_sites(
            session,
            args.dir,
            'https://www.sepaq.com/en/reservation/camping/init?type=Pr%C3%AAt%20%C3%A0%20camper'
        )

        with campsites_file.open('w') as fp:
            json.dump(data, fp, indent=2)
    elif args.parse:
        # load campsites data
        with campsites_file.open() as fp:
            campsites = json.load(fp)

        # find availability files of all campsites
        filepaths = sorted(args.dir.rglob('availabilities.json'))

        last_park = None
        # optional
        last_sub_park = None
        last_camp_site = None

        # TODO: it would be better to iterate over data from campsites (needs to be recursive)
        # that way the park structure also doesn't have to be replicated on the file system
        # ie, could just store availabilities in one directory and assign some ID which is stored in campsites.json
        for filepath in filepaths:
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

            with filepath.open() as fp:
                data = json.load(fp)

                filtered_data = {}

                for entry in data:
                    date_string = entry['dateAsStandardString']
                    date = datetime.date.fromisoformat(date_string)

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

                    if len(group) >= min_days:
                        print(f'<li>{min(group)} to {max(group)}</li>')

                print('</ul>')

            last_park = park
            last_sub_park = sub_park
            last_camp_site = camp_site
