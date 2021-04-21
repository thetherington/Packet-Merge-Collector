import copy
import json
from threading import Thread

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.packages.urllib3.disable_warnings()


class MagnumCache:
    def __init__(self, **kwargs):

        self.nature = "mag-1"
        self.cluster_ip = None
        self.insite = None
        self.device_types = []

        for key, value in kwargs.items():

            if value:
                setattr(self, key, value)

        self.cache_url = "http://{}/proxy/insite/{}/api/-/model/magnum/{}".format(
            self.insite, self.nature, self.cluster_ip
        )

        self.edge_dict = self.catalog_cache()

        # print(json.dumps(self.edge_dict, indent=1))

    def return_mnemonics(self, host, decoder):

        try:
            return self.edge_dict[host]["mnemonics"][decoder]

        except Exception:
            return {}

    def config_fetch(self):

        try:

            response = requests.get(self.cache_url, verify=False, timeout=30.0)

            return json.loads(response.text)

        except Exception as e:
            print(e)

        return None

    def catalog_cache(self):

        edge_dict = {}

        config = self.config_fetch()

        if config:

            for device in config["magnum"]["magnum-controlled-devices"]:

                if device["device"] in self.device_types:

                    edge_template = {
                        "s_device_name": device["device-name"],
                        "s_device": device["device"],
                        "s_device_size": device["device-size"],
                        "s_device_type": device["device-type"],
                        "s_control_1_address": device["control-1-address"]["host"],
                        "mnemonics": {},
                    }

                    if "control-2-address" in device.keys():

                        edge_template.update(
                            {"s_control_2_address": device["control-2-address"]["host"]}
                        )

                    for count, stream in enumerate(device["streams"], 1):

                        if stream["general"]["direction"] == "out" and "mnemonics" in stream.keys():

                            mnemonics_template = {count: {}}

                            for mnemonic in stream["mnemonics"]:

                                mnemonics_template[count].update(
                                    {
                                        "s_"
                                        + mnemonic["interface"]
                                        .lower()
                                        .replace(" ", "_"): mnemonic["mnemonic"]
                                    }
                                )

                            edge_template["mnemonics"].update(mnemonics_template)

                    edge_dict.update({edge_template["s_control_1_address"]: edge_template})

        return edge_dict


class PacketMergeCollector:
    def __init__(self, **kwargs):

        self.decoders = []
        self.hosts = []
        self.proto = "http"
        self.magnum = None

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

            if "magnum" in key and value:
                self.magnum = MagnumCache(**value)

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

            # if magnum lookup is enable, iterate through each decoder
            # update the decoder definition with mnemonics.
            # function return_mnemonics returns {} if lookup fails.
            if self.magnum:

                for decoder, params in decoders.items():

                    params.update(self.magnum.return_mnemonics(host, decoder))

            collection.update(host_decoders)

        except Exception:
            pass

    @property
    def collect(self):

        collection = {}

        threads = [
            Thread(target=self.parse_results, args=(host, collection,)) for host in self.hosts
        ]

        for x in threads:
            x.start()

        for y in threads:
            y.join()

        return collection


def main():

    params = {
        "hosts": ["192.168.0.16"],
        "decoders": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "magnum": {
            "insite": "172.16.205.203",
            "cluster_ip": "192.168.0.250",
            "device_types": ["SCORPION-X18-APP-J2K-8E2D", "570J2K-U9D"],
        },
    }

    collector = PacketMergeCollector(**params)

    documents = []

    for host, decoders in collector.collect.items():

        for _, params in decoders.items():

            document = {"fields": params, "host": host, "name": "merged"}

            documents.append(document)

    print(json.dumps(documents, indent=1))


if __name__ == "__main__":
    main()
