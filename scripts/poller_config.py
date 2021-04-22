import json
from insite_plugin import InsitePlugin
from packet_merge import PacketMergeCollector


class Plugin(InsitePlugin):
    def can_group(self):
        return True

    def fetch(self, hosts):

        try:

            self.collector

        except Exception:

            params = {
                "hosts": hosts,  # "auto", - to auto find hosts by magnum config,
                "decoders": [1, 2, 3, 4, 5, 6, 7, 8, 9],
                "magnum": {
                    "insite": "172.16.205.203",
                    "cluster_ip": "192.168.0.250",
                    "device_types": ["SCORPION-X18-APP-J2K-8E2D", "570J2K-U9D"],
                },
            }

            self.collector = PacketMergeCollector(**params)

        documents = []

        for ip, decoders in self.collector.collect.items():

            for _, params in decoders.items():

                document = {"fields": params, "host": ip, "name": "merged"}

                documents.append(document)

        return json.dumps(documents)

