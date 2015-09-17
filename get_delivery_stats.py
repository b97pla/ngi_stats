import datetime
import json
import os
import pandas
import re
import requests

__author__ = 'Pontus'


def get_stats():

    def get_projects(session, headers, base_url):
        url = "{}/projects".format(base_url)
        rq = session.get(url, headers=headers)
        return rq.json().get('projects')

    def get_samples(session, headers, base_url, projectid=None):
        url = "{}/samples/{}".format(base_url, projectid)
        rq = session.get(url, headers=headers)
        return rq.json().get('samples')

    def get_seqruns(session, headers, base_url, projectid=None, sampleid=None):
        url = "{}/seqruns/{}/{}".format(base_url, projectid, sampleid)
        rq = session.get(url, headers=headers)
        return rq.json().get('seqruns')

    def get_delivery_date(session, headers, base_url, entry=None):
        logs = filter(
            lambda x: 'delivery_status' in x.get('changed') and x['changed']['delivery_status'] == 'DELIVERED',
            _get_logs(session,headers,base_url,entry=entry))
        return _get_latest(logs)

    def get_analysis_date(session, headers, base_url, entry=None):
        logs = filter(
            lambda x: 'analysis_status' in x.get('changed') and x['changed']['analysis_status'] == 'ANALYZED',
            _get_logs(session,headers,base_url,entry=entry))
        return _get_latest(logs)

    def get_status_date(session, headers, base_url, entry=None):
        logs = filter(
            lambda x: 'status' in x.get('changed') and x['changed']['status'] in ['SEQUENCED'],
            _get_logs(session,headers,base_url,entry=entry))
        return _get_latest(logs)

    def _get_latest(logs):
        if logs:
            return max(map(lambda x: _parse_date(x.get('timestamp')), logs))

    def _parse_date(datestr, frmt=None):
        return datetime.datetime.strptime(datestr,frmt or "%Y-%m-%dT%H:%M:%S.%fZ")

    def _get_logs(session, headers, base_url, entry=None):
        url = filter(lambda x: x.get('rel','') == 'logs', entry.get('links',[]))[0].get('href')
        rq = session.get(url, headers=headers)
        return rq.json().get('logs')

    def _sequencing_facility(facility_desc, project_id):
        if facility_desc == 'NGI-U' or re.match("^[A-Z]{2}-?\d{2,4}$",project_id):
            return 'NGI-U'
        return 'NGI-S'

    picklefile = os.path.join('data', '{}_samples.pandas'.format(datetime.date.today().strftime("%Y-%m-%d")))
    samples = []
    if not os.path.exists(picklefile):
        session = requests.Session()
        headers = {'X-Charon-API-token': os.getenv('CHARON_API_TOKEN'),'content-type': 'application/json'}
        base_url = "{}/api/v1".format(os.getenv('CHARON_BASE_URL').replace('-dev',''))
        args = [session, headers, base_url]
        for project in get_projects(*args):
            for sample in get_samples(*args, projectid=project.get('projectid')):
                seqruns = get_seqruns(*args, projectid=project.get('projectid'), sampleid=sample.get('sampleid'))
                samples.append({
                    'project': project.get('projectid'),
                    'sample': sample.get('sampleid'),
                    'sequencing_facility': project.get('sequencing_facility'),
                    'project_status': project.get('status'),
                    'project_status_date': get_status_date(*args, entry=project),
                    'sample_status': sample.get('status'),
                    'sample_status_date': get_status_date(*args, entry=sample),
                    'sample_analysis_status': sample.get('analysis_status'),
                    'sample_analysis_date': get_analysis_date(*args, entry=sample),
                    'project_delivery_status': project.get('delivery_status'),
                    'sample_delivery_status': sample.get('delivery_status'),
                    'project_delivery_date': get_delivery_date(*args, entry=project),
                    'sample_delivery_date': get_delivery_date(*args, entry=sample),
                    'seqruns': map(lambda x:
                                   {'seqrunid': x.get('seqrunid'),
                                    'timestamp': x.get('created')}, seqruns),
                    'count': 1
                })
                samples[-1]['sample_sequence_date'] = _get_latest(samples[-1]['seqruns'])
        samplef = pandas.DataFrame(samples)
        samplef.to_pickle(picklefile)
        plots = {
            'sequenced_samples': {
                'index': 'sample_sequence_date',
            },
            'analyzed_samples': {
                'index': 'sample_analysis_date',
            },
            'delivered_samples': {
                'index': 'sample_delivery_date',
            },
        }

        drange = pandas.date_range(start=datetime.datetime(2015,1,1), periods=52, freq='W')

        for title in plots.keys():
            jsonfile = os.path.join("data", "{}.json".format(title))
            # re-index using the timestamps
            col = plots[title]['index']
            df = samplef[[col,'sequencing_facility','project','count']].dropna().set_index(col)
            # get aggregate statistics per week for each facility
            per_week_u = df[df.apply(lambda x: _sequencing_facility(x['sequencing_facility'], x['project']) == 'NGI-U', axis=1)]['count'].resample('W', how=sum).dropna()
            per_week_s = df[df.apply(lambda x: _sequencing_facility(x['sequencing_facility'], x['project']) == 'NGI-S', axis=1)]['count'].resample('W', how=sum).dropna()
            per_week = {'NGI-U': per_week_u, 'NGI-S': per_week_s}

            with open(jsonfile,'w') as fh:
                json.dump(
                    map(
                        lambda node: {'key': node, 'values': map(
                            lambda d: [
                                (d - datetime.datetime(1970,1,1)).total_seconds(),
                                per_week[node].get(d,0) or 0],
                            drange)},
                        per_week.keys()),
                    fh)

if __name__ == "__main__":
    get_stats()
