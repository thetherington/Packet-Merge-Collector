import copy
import json

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.packages.urllib3.disable_warnings()


class PacketMergeCollector:
    def __init__(self, **kwargs):

        self.decoders = []
        self.hosts = []
        self.proto = "http"

        self.playout_status = {"id": "364.<replace>@i", "type": "integer", "name": "Playout Status"}
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
                    "%s://%s/login.php" % (self.proto, host), verify=False, timeout=30.0,
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
                    url, headers=headers, data=json.dumps(payload), verify=False, timeout=30.0,
                )

                return json.loads(response.text)

        except Exception as error:
            return error


def main():

    params = {"hosts": ["192.168.0.16"], "decoders": [1, 2]}

    collector = PacketMergeCollector(**params)

    # print(json.dumps(collector.parameters, indent=1))

    print(collector.fetch(collector.hosts[-1]))


if __name__ == "__main__":
    main()
