import argparse
import csv
import json

from data.processing import load_domain_data

THIRD_PARTY_SERVICES = {
    'fonts.googleapis.com': 'Google Fonts',
    'www.google-analytics.com': 'Google Analytics',
    'Digital Analytics Program': 'dap.digitalgov.gov'
}

CUSTOMER_SATISFACTION_TOOLS = {
    'iperceptions01.azureedge.net': 'iPerceptions',
    'ips-invite.iperceptions.com': 'iPerceptions',
    'universal.iperceptions.com': 'iPerceptions',
    'api.iperceptions.com': 'iPerceptions',
    'health.foresee.com': 'Foresee',
    'events.foreseeresults.com': 'Foresee',
    'script.hotjar.com': 'Hotjar',
    'static.hotjar.com': 'Hotjar',
    'vars.hotjar.com': 'Hotjar',
    'js.hs-analytics.net': 'HHS Voice of Customer Tool',
    'api.mixpanel.com': 'Mixpanel',
    'siteintercept.qualtrics.com': 'Qualtrics',
    'assets01.surveymonkey.com': 'SurveyMonkey',
    'secure.surveymonkey.com': 'SurveyMonkey',
    'by2.uservoice.com': 'UserVoice'
}

CUSTOMER_SATISFACTION_URLS = {
    'iPerceptions': 'https://www.iperceptions.com',
    'Foresee': 'https://www.foresee.com',
    'Hotjar': 'https://www.hotjar.com',
    'HHS Voice of Customer Tool': 'https://www.hhs.gov',
    'Mixpanel': 'https://mixpanel.com',
    'Qualtrics': 'https://www.qualtrics.com',
    'SurveyMonkey': 'https://www.surveymonkey.com',
    'UserVoice': 'https://www.uservoice.com'
}


def process_cust_sat(third_parties_file, pshtt_file):
    #load_data
    raw_data = load_data(third_parties_file)
    #load_pshtt
    pshtt_data = load_data(pshtt_file)
    scanned = [row['Domain'] for row in raw_data]
    pshtt_data = [row for row in pshtt_data if row.get('Domain') in scanned]
    #create_domain_map
    domains, agencies, _ = load_domain_data()
    #create_domain_data
    scan_data = create_domain_data(raw_data, pshtt_data, domains)
    #process_domain_data
    domain_report = process_domain_data(scan_data)
    agency_report = create_agency_totals(domain_report, agencies)
    totals = {
        'eligible': len(domain_report['data']),
        'participating': len([domain for domain in domain_report['data']
                             if domain['participating'] == True])}
    return domain_report, agency_report, totals


def load_data(cs_file):
    with open(cs_file, 'r') as f:
        records = csv.DictReader(f)
        return [row for row in records]

def create_domain_data(raw_data, pshtt_data, domains):
    domain_data = {domain: {} for domain in domains}

    for row in raw_data:
        domain = row['Domain']
        if not domains.get(domain):
            continue
        domain_data[domain]['cust_sat'] = row

    for row in pshtt_data:
        domain = row['Domain']
        if not domains.get(domain):
            continue
        domain_data[domain]['pshtt'] = row
        domain_data[domain]['live'] = row['Live']
        domain_data[domain]['branch'] = domains[domain]['branch']
        domain_data[domain]['redirect'] = row['Redirect']
        domain_data[domain]['agency_name'] = domains[domain]['agency_name']
        domain_data[domain]['agency_slug'] = domains[domain]['agency_slug']
        domain_data[domain]['canonical'] = row['Canonical URL']

    # These are temporary hacks. Get rid of them.
    domain_data = {s:domain_data[s] for s in domain_data if domain_data[s] != {}
                   and set(['pshtt', 'cust_sat']).issubset(domain_data[s].keys())}
    return domain_data

def process_domain_data(scan_data):
    reports = {'data':[]}

    for domain_name, domain in scan_data.items():
        if eligible_for_customer_satisfaction(domain):
            external_domains = [x.strip() for x in domain['cust_sat']['External Domains'].split('|')]
            cust_sat_tools = [CUSTOMER_SATISFACTION_TOOLS[x] for x in external_domains if x in CUSTOMER_SATISFACTION_TOOLS]
            result = {
                'participating': len(cust_sat_tools) > 0,
                'service-list': {s: CUSTOMER_SATISFACTION_URLS[s] for s in cust_sat_tools},
                'agency_slug': domain['agency_slug'],
                'agency_name': domain['agency_name'],
                'canonical': domain['canonical'],
                'domain': domain_name
            }
            reports['data'].append(result)
    return reports

def create_agency_totals(domain_report, agencies):
    reports = {'data': []}
    results = {}
    for agency_key, agency in agencies.items():
        results[agency_key] = {
            'name': agency['name'],
            'eligible': 0,
            'participating': 0
        }
    for domain in domain_report['data']:
        results[domain['agency_slug']]['eligible'] += 1
        if domain['participating']:
            results[domain['agency_slug']]['participating'] += 1

    for k, v in results.items():
        if v['eligible']:
            reports['data'].append(v)
    return reports


def eligible_for_customer_satisfaction(domain):
    return (
        (domain['live'] == 'True') and
        (domain['redirect'] == 'False') and
        (domain['branch'] == 'executive')
    )

if __name__ =='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cust_sat', required=True)
    parser.add_argument('--pshtt', required=True)
    args = parser.parse_args()

    domains, agencies, customer_satisfaction = process_cust_sat(args.cust_sat,
                                                                args.pshtt)
    with open('domains.json', 'w+') as f:
        json.dump(domains, f, indent=2)
    with open('agencies.json', 'w+') as f:
        json.dump(agencies, f, indent=2)
    with open('customer_satisfaction.json', 'w+') as f:
        json.dump(customer_satisfaction, f, indent=2)
