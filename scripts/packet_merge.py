import copy
import json
from threading import Thread

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.packages.urllib3.disable_warnings()


class PacketMergeCollector:
    def __init__(self, **kwargs):

        self.decoders = []
        self.hosts = []
        self.proto = "http"

        self.link_select = {"id": "361.<replace>@i", "type": "integer", "name": "link_select"}
        self.playout_status = {"id": "364.<replace>@i", "type": "integer", "name": "playout_status"}
        self.main_drop = {
            "id": "301.<replace>.0@i",
            "type": "integer",
            "name": "l_main_packet_drop",
        }
        self.main_rate = {
            "id": "302.<replace>.0@i",
            "type": "integer",
            "name": "l_main_packet_rate",
        }
        self.backup_drop = {
            "id": "301.<replace>.1@i",
            "type": "integer",
            "name": "l_backup_packet_drop",
        }
        self.backup_rate = {
            "id": "302.<replace>.1@i",
            "type": "integer",
            "name": "l_backup_packet_rate",
        }
        self.hitless_drop = {
            "id": "301.<replace>.2@i",
            "type": "integer",
            "name": "l_hitless_packet_drop",
        }
        self.hitless_rate = {
            "id": "302.<replace>.2@i",
            "type": "integer",
            "name": "l_hitless_packet_rate",
        }

        self.link_select_lookup = {
            0: "Auto Packet Merge",
            1: "SFP 10G Main",
            2: "SFP 10G Backup",
            3: "Fail Over",
            4: "Dual Source Switch Mode",
        }
        self.status_lookup = {0: "Merged", 1: "Main", 2: "Backup"}

        self.parameters = []

        for key, value in kwargs.items():

            if "hosts" in key and value:
                self.hosts.extend(value)

            if "decoders" in key and value:
                self.decoders.extend(value)

            if "proto" in key and value:
                self.proto = value

        for decode in self.decoders:

            for template in [
                self.link_select,
                self.playout_status,
                self.main_drop,
                self.main_rate,
                self.backup_drop,
                self.backup_rate,
                self.hitless_drop,
                self.hitless_rate,
            ]:

                template_copy = copy.deepcopy(template)

                template_copy["id"] = template_copy["id"].replace("<replace>", str(decode - 1))

                self.parameters.append(template_copy)

    def fetch(self, host):

        try:

            with requests.Session() as session:

                ## get the session ID from accessing the login.php site
                resp = session.get(
                    "%s://%s/login.php" % (self.proto, host), verify=False, timeout=15.0,
                )

                session_id = resp.headers["Set-Cookie"].split(";")[0]

                payload = {
                    "jsonrpc": "2.0",
                    "method": "get",
                    "params": {"parameters": self.parameters},
                    "id": 1,
                }

                url = "%s://%s/cgi-bin/cfgjsonrpc" % (self.proto, host)

                headers = {
                    "Content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Cookie": session_id + "; webeasy-loggedin=true",
                }

                response = session.post(
                    url, headers=headers, data=json.dumps(payload), verify=False, timeout=15.0,
                )

                return json.loads(response.text)

        except Exception as error:
            return error

    def parse_results(self, host, collection):

        # inital tree
        host_decoders = {host: {}}

        # reference in
        decoders = host_decoders[host]

        results = self.fetch(host)
        # print(results)
        # from response import params

        # results = params

        try:

            for result in results["result"]["parameters"]:

                # seperate "240.1@i" to "1" or 301.2.0@i to "2"
                _instance = result["id"].split(".")[1][:1]

                # upconvert base 0 to base 1
                _instance = int(_instance) + 1

                # convert to bit rate from kbps
                if "packet_rate" in result["name"]:
                    result["value"] = result["value"] * 1000

                # perform lookup for playout status enumeration
                elif "playout_status" in result["name"]:
                    result["value"] = self.status_lookup[result["value"]]

                # perform lookup for link select enumeration
                elif "link_select" in result["name"]:
                    result["value"] = self.link_select_lookup[result["value"]]

                if _instance not in decoders.keys():

                    decoders.update(
                        {
                            _instance: {
                                result["name"]: result["value"],
                                "i_decoder": _instance,
                                "as_ids": [result["id"]],
                            }
                        }
                    )

                else:

                    decoders[_instance].update({result["name"]: result["value"]})
                    decoders[_instance]["as_ids"].append(result["id"])

            collection.update(host_decoders)

        except Exception as e:
            pass

    def collect(self):

        collection = {}

        threads = [
            Thread(target=self.parse_results, args=(host, collection,)) for host in self.hosts
        ]

        for x in threads:
            x.start()

        for y in threads:
            y.join()

        print(json.dumps(collection, indent=1))


def main():

    params = {"hosts": ["192.168.0.16"], "decoders": [1, 2, 3, 4, 5, 6, 7, 8, 9]}

    collector = PacketMergeCollector(**params)

    # print(json.dumps(collector.parameters, indent=1))

    # print(collector.fetch(collector.hosts[-1]))

    # collector.parse_results(collector.hosts[-1])

    collector.collect()


if __name__ == "__main__":
    main()
