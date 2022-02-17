from ncclient import manager
import xmltodict
import os
from datetime import datetime, timezone
from flask import Flask, render_template, request
import humanfriendly


app = Flask(__name__)

def get_client_data(data: dict, client_mac: str, key: str = 'client-mac') -> dict:
    for client_data in data:
        if client_data[key] == client_mac:
            return client_data
    return {}

def client(
    host: str, port: int = 830, username: str = '', password: str = '', client_ip: str = ''
) -> dict:
    # NETCONF Connection Manager
    with manager.connect(
        host=host,
        port=port,
        username=username,
        password=password,
        hostkey_verify=False,
        device_params={'name': 'iosxe'},
    ) as m:  # type: ignore

        # See https://community.cisco.com/t5/nso-developer-hub-discussions/how-to-get-wireless-clients-connected-to-c9800-installed-netconf/td-p/4107720
        # Add xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" to the filter tag
        client_oper_data_filter = '''
            <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
                <client-oper-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-wireless-client-oper"/>
            </filter>
        '''

        # Execute the netconf get
        result = m.get(client_oper_data_filter).data_xml
        client_oper_data = xmltodict.parse(result)['data']['client-oper-data']
        if not client_oper_data:
            raise ValueError('error getting client oper data')

        # Derive the client MAC from the IP
        client_mac = None
        client_ipv6 = None
        for client in client_oper_data['sisf-db-mac']:
            if client['ipv4-binding']['ip-key']['ip-addr'] == client_ip:
                client_mac = client['mac-addr']
                if type(client['ipv6-binding']) is list:
                    client_ipv6 = ''
                    for item in client['ipv6-binding']:
                        client_ipv6 += item['ip-key']['ip-addr'] + ' '
                else:
                    client_ipv6 = client['ipv6-binding']['ip-key']['ip-addr']
                break

        if not client_mac:
            raise ValueError('error getting client MAC from IP')

        common_oper_data = get_client_data(client_oper_data['common-oper-data'], client_mac)
        client_history = get_client_data(client_oper_data['mm-if-client-history'], client_mac)
        traffic_stats = get_client_data(
            client_oper_data['traffic-stats'], client_mac, key='ms-mac-address'
        )
        policy_data = get_client_data(client_oper_data['policy-data'], client_mac, key='mac')
        dc_info = get_client_data(client_oper_data['dc-info'], client_mac)
        dot11_oper_data = get_client_data(
            client_oper_data['dot11-oper-data'], client_mac, key='ms-mac-address'
        )

        return {
            'client_ipv6': client_ipv6,
            'common_oper_data': common_oper_data,
            'client_history': client_history,
            'traffic_stats': traffic_stats,
            'policy_data': policy_data,
            'dc_info': dc_info,
            'dot11_oper_data': dot11_oper_data,
        }


@app.route('/')
def hello():
    host = os.environ['HOST']
    username = os.environ['USERNAME']
    password = os.environ['PASSWORD']
    client_ip = request.environ['REMOTE_ADDR']
    print(client_ip)

    raw_client_info = client(host=host, username=username, password=password, client_ip=client_ip)
    client_info = {}
    client_info['AP'] = raw_client_info['common_oper_data']['ap-name']
    client_info['IPv4'] = client_ip
    client_info['IPv6'] = raw_client_info['client_ipv6']
    client_info['VLAN'] = raw_client_info['dot11_oper_data']['ms-wlan-id']
    client_info['Signal Strength'] = raw_client_info['traffic_stats']['most-recent-rssi']
    client_info['Signal Quality'] = raw_client_info['traffic_stats']['most-recent-snr']
    client_info['Connection Speed'] = raw_client_info['traffic_stats']['speed'] + ' mbps'
    client_info['Frequency'] = raw_client_info['common_oper_data']['ms-radio-type']
    client_info['Channel'] = raw_client_info['dot11_oper_data']['current-channel']
    dc_info = raw_client_info['dc_info']
    client_info[
        'Device Type'
    ] = f"{dc_info['device-vendor']} {dc_info['device-name']} {dc_info['device-os']}"
    client_info['SSID'] = raw_client_info['dot11_oper_data']['vap-ssid']
    client_info['Bytes Total'] = humanfriendly.format_size(
        int(raw_client_info['traffic_stats']['bytes-rx'])
        + int(raw_client_info['traffic_stats']['bytes-tx']),
        binary=True,
    )
    client_info_roaming = []
    roaming_history = raw_client_info['client_history']['mobility-history']['entry']
    for raw_entry in roaming_history:
        utc_timestamp = datetime.strptime(raw_entry['ms-assoc-time'], '%Y-%m-%dT%H:%M:%S+00:00')
        est_timestamp = utc_timestamp.replace(tzinfo=timezone.utc).astimezone(tz=None)
        client_info_roaming.append(
            {
                'AP': raw_entry['ap-name'],
                'Time': est_timestamp.strftime('%-m/%-d/%y %-I:%M:%S %p'),
                'Type': raw_entry['dot11-roam-type'].removeprefix('dot11-roam-type-'),
            }
        )

    return render_template(
        'client_info.html', client_info=client_info, client_info_roaming=client_info_roaming
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
