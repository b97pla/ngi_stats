import datetime
import json
import os

__author__ = 'Pontus'


class SizeLogParser(object):

    def __init__(self, logfile):
        self.logfile = logfile
        self.jsonfile = os.path.join(
            os.path.dirname(__file__), 'data', 'ngi_project_sizes.json')
        with open(self.logfile) as fh:
            self.sizes = SizeLogParser.parse_log(fh)
        self.dump_json()

    @staticmethod
    def parse_log(fh):
        def _extract_data(x):
            try:
                [datestr, timestr, project, path, size] = x.split()
            except ValueError:
                return None, None, None
            tstamp = (datetime.datetime.strptime(
                "{}T{}".format(datestr, timestr[0:-6]),
                "%Y-%m-%dT%H:%M:%S") -
                      datetime.datetime(1970,1,1)).total_seconds()
            return project, tstamp, size

        project_sizes = {}
        for project, tstamp, size in map(_extract_data, fh):
            if project is None:
                continue
            if project not in project_sizes:
                project_sizes[project] = []
            project_sizes[project].append((tstamp, int(size)))

        def _reformat_arr(x):
            return {'key': x, 'values': sorted(project_sizes[x], cmp=lambda x,y: x < y, key=lambda x: x[0])}

        return map(_reformat_arr, project_sizes.keys())

    def dump_json(self):
        with open(self.jsonfile, 'w') as fh:
            json.dump(self.sizes, fh)


if __name__ == "__main__":
    SizeLogParser(os.path.join('data', 'project_sizes.txt'))
