# inSITE Multi Path Packet Merge Collector

The Multi Path Packet Merge (MPPM) collector is a data collection module that gathers MPPM settings and status from edge devices in a SDVN network.  The poller script uses the cfgjsonrpc webeasy program to gather information.   

The data collection module has the below distinct abilities and features:

1. Collects Main, Backup, and Hitless input information like bit rate and dropped packets
2. Collects the playout status and link select status.
3. Collects from multiple decoders for a device at the same time.
4. Multi-threaded for multiple devices for non blocking capability.
5. Texutal status values for easy use with the Intelligence notifications.
6. Supports auto lookup annotations of magnum destination label mnemonics.

## Minimum Requirements:

- inSITE Version 10.3 and service pack 6
- Python3.7 (_already installed on inSITE machine_)
- Python3 Requests library (_already installed on inSITE machine_)

## Installation:

Installation of the status monitoring module requires copying two scripts into the poller modules folder:

1. Copy __packet_merge.py__ script to the poller python modules folder:
   ```
    cp scripts/process_monitor.py /opt/evertz/insite/parasite/applications/pll-1/data/python/modules
   ```

2. Restart the poller application

## Configuration:

To configure a poller to use the module start a new python poller configuration outlined below

1. Click the create a custom poller from the poller application settings page
2. Enter a Name, Summary and Description information
3. Enter the host value in the _Hosts_ tab
4. From the _Input_ tab change the _Type_ to __Python__
5. From the _Input_ tab change the _Metric Set Name_ field to __packetmerge__
6. From the _Python_ tab select the _Advanced_ tab and enable the __CPython Bindings__ option
7. Select the _Script_ tab, then paste the contents of __scripts/poller_config.py__ into the script panel.

8. Locate the below section of the script for custom modifcations:
   ```
      params = {
            "hosts": hosts,
            "decoders": [1, 2, 3, 4, 5, 6, 7, 8, 9],
            "magnum": {
               "insite": "172.16.205.203",
               "cluster_ip": "192.168.0.250",
               "device_types": ["SCORPION-X18-APP-J2K-8E2D", "570J2K-U9D"],
            },
      }
   ```
   
   Update the decoder list with the number of decoders the device has or uses.
   
   If there's a need to annotate the decoder collection with the magnum destination mnemonics, then update the following in the __magnum__ parameter object:

   - __insite__ - ip address of the insite server.
   - __cluster_ip__ - the cluster ip address of the magnum server.
   - __device_types__ - a list of devices to cache the mnemonic label collection (less is better).

   If there's no need for the magnum destination mnemonics lookup, then you can comment out the __magnum__ parameter options.

9.  Save changes, then restart the poller program.

## Testing:

The process_monitor script can be ran manually from the shell using the following command
```
python packet_merge.py
```

Below is the sample json file created:

```
 {
  "fields": {
   "link_select": "Auto Packet Merge",
   "i_decoder": 1,
   "as_ids": [
    "361.0@i",
    "364.0@i",
    "301.0.0@i",
    "302.0.0@i",
    "301.0.1@i",
    "302.0.1@i",
    "301.0.2@i",
    "302.0.2@i"
   ],
   "playout_status": "Merged",
   "l_main_packet_drop": 32845644,
   "l_main_packet_rate": 250757000,
   "l_backup_packet_drop": 1363,
   "l_backup_packet_rate": 250757000,
   "l_hitless_packet_drop": 631,
   "l_hitless_packet_rate": 250757000,
   "s_global": "G2-DEC17",
   "s_description": "DEC-47A11-RX-37"
  },
  "host": "192.168.0.16",
  "name": "merged"
 }
```