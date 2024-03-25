import requests
import json
import subprocess
import re


class Website_IP_Tracer:
    def __init__(self, website, end_point):
        self.website = website
        self.endpoint = end_point
        self.IP_list = []

    def trace_and_find_ip(self):
        try:
            hop_counter = 0
            tracer = subprocess.Popen(
                ["tracert", self.website],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            IP_reg = re.compile(r"(?P<IP>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")

            while hop_counter < 10:
                for line in tracer.stdout:
                    line = line.decode('cp866')
                    print(line)
                    match_ip = IP_reg.search(line)
                    if match_ip and '*' not in line:
                        self.IP_list.append(match_ip.group('IP'))
                        hop_counter += 1
                    elif '*' in line:
                        break

                if '*' in line:
                    break

            initial_ip = self.IP_list[0]
            self.IP_list.pop(0)
            self.IP_list.append(initial_ip)
            self.find_ip()
            tracer.wait()

        except Exception as ex:
            print(ex)

    def find_ip(self):
        try:
            data = json.dumps(self.IP_list)
            response = requests.post(self.endpoint, data=data)
            response = response.json()
            print(response)
            for item in response:
                if (
                    'org' in item.keys()
                    and 'query' in item.keys()
                    and 'city' in item.keys()
                    and 'country' in item.keys()
                ):
                    print(
                        item['org'] + ' has an ip '
                        + item['query'] + ' is in '
                        + item['city'] + ', '
                        + item['country']
                    )
                else:
                    print(item['query'])
            raise Exception
        except Exception as ex:
            print(ex)


def main():
    website = "your_link"
    end_point = "http://ip-api.com/batch"
    tracer = Website_IP_Tracer(website, end_point)
    tracer.trace_and_find_ip()


if __name__ == "__main__":
    main()
