from __future__ import annotations
from typing import Union
from dnslib import A, DNSRecord, QTYPE, RR
import json
import socket
import time


class cacheDNS:

    DNS_IP_list = ["199.7.83.42", "193.0.14.129", "202.12.27.33"
                   "192.58.128.30", "198.97.190.53", "192.36.148.17",
                   "185.228.168.9", "185.121.177.177", "45.32.230.225",
                   "198.97.190.53", "192.36.148.17", "192.58.128.30"]

    def __init__(self, host: str):
        self.cache: set = {}
        self.retrieve()
        self.socket: socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((host, 53))
        self.q_type: Union[None, str] = None

    def get_response(self, record_dns: DNSRecord):
        name = record_dns.q.qname.__str__()
        index = name.find('multiply')
        zones = name[:index].split('.')
        sch = 0

        for zone in zones:
            try:
                current_zone = int(zone)
                if sch == 0:
                    sch = 1
                sch *= current_zone
            except ValueError:
                continue

        sch %= 256
        ip_reply = f'127.0.0.{sch}'
        reply = record_dns.reply()
        reply.add_answer(RR(record_dns.q.qname, QTYPE.A, rdata=A(ip_reply), ttl=60))

        return reply.pack()

    def get_records(self, dns_record: DNSRecord, name: str):
        reply = dns_record.reply()
        current_time = time.time()

        for result in self.cache[name]:
            if result[2] + result[1] - current_time >= 0:
                rr = RR(rname=name, rtype=QTYPE.A,
                        rdata=A(result[0]), ttl=result[1])
                reply.add_answer(rr)

        return reply

    def update_cache_data(self):
        with open('cache_result.json', 'w') as cache:
            json.dump(self.cache, cache)

    def retrieve(self):
        try:
            with open('cache_result.json', 'r') as cache:
                data = json.load(cache)
                if data:
                    self.cache = data
        except FileNotFoundError:
            self.update_cache_data()

    def data_result(self, request: str, result: DNSRecord):
        answers = []

        for rr in result.rr:
            answers.append((rr.rdata.__str__(), rr.ttl, time.time()))

        if len(answers) == 0:
            return
        
        self.cache[request] = answers
        self.update_cache_data()

    def get_new_ip_zones(self, parsed_response: DNSRecord):
        new_zones_ip = []

        for address in parsed_response.ar:
            if address.rtype == 1:
                new_zones_ip.append(address.rdata.__repr__())

        if len(new_zones_ip) == 0:
            for address in parsed_response.auth:
                if address.rtype == 2:
                    question = DNSRecord.question(address.rdata.__repr__())
                    pkt = self.lookup(question, cacheDNS.DNS_IP_list[0])
                    parsed_pkt = DNSRecord.parse(pkt)
                    new_zone_ip = parsed_pkt.a.rdata.__repr__()
                    if new_zone_ip:
                        new_zones_ip.append(new_zone_ip)

        return new_zones_ip

    def lookup(self, dns_record: DNSRecord, zone_ip: str):
        response = dns_record.send(zone_ip)
        parsed_response = DNSRecord.parse(response)

        for address in parsed_response.auth:
            if address.rtype == 6:
                return response

        if parsed_response.a.rdata:
            return response
        new_zones_ip = self.get_new_ip_zones(parsed_response)

        for new_zone_ip in new_zones_ip:
            ip = self.lookup(dns_record, new_zone_ip)
            if ip:
                return ip

        return None

    def server_work(self):
        while True:
            data, addr = self.socket.recvfrom(512)
            record_dns = DNSRecord.parse(data)
            q_name = record_dns.q.qname.__str__()

            if record_dns.q.qtype != 1:
                self.socket.sendto(data, addr)

            elif 'multiply' in q_name:
                self.socket.sendto(self.get_response(record_dns), addr)

            else:
                if q_name in self.cache:

                    reply = self.get_records(record_dns, q_name)

                    if reply.a.rdata:
                        self.socket.sendto(reply.pack(), addr)
                        continue

                    else:
                        del self.cache[q_name]

                result = None

                for root_server in cacheDNS.DNS_IP_list:
                    self.q_type = record_dns.q.qtype
                    result = self.lookup(record_dns, root_server)
                    if result:
                        break

                self.data_result(q_name, DNSRecord.parse(result))
                self.socket.sendto(result, addr)


if __name__ == "__main__":
    cacheDNS('127.0.0.1').server_work()
