""" Copyright (c) 2020 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
           https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied. 
"""

from aiohttp import TraceResponseChunkReceivedParams
import requests, json, time, os

# Get the list of templates
def get_templates(host, token):
    headers = {
              'content-type': "application/json",
              'x-auth-token': token
          }

    url = "https://{}/dna/intent/api/v1/template-programmer/template".format(host)
    resp = requests.get(url, headers=headers, verify=False)

    return resp.json()

# Get the list of switches
def get_switches(host, token):
    headers = {
              'content-type': "application/json",
              'x-auth-token': token
          }

    url = "https://{}/dna/intent/api/v1/network-device".format(host)
    resp = requests.get(url, headers=headers, verify=False)

    result = []
    for device in resp.json()['response']:
        if device['family'] == "Switches and Hubs":
            result += [device]
    
    return result

# Apply a template to a given switch with given parameters
def apply_template(params, device_id, host, token):
    TEMPLATE_NAME = os.environ['TEMPLATE_NAME']
    template_id = get_id_for_template(TEMPLATE_NAME, host, token)
    headers = {
              'content-type': "application/json",
              'x-auth-token': token
          }

    url = "https://{}/dna/intent/api/v2/template-programmer/template?id={}".format(host, template_id)
    resp = requests.get(url, headers=headers, verify=False)
    
    body = {
        "forcePushTemplate": True,
        "targetInfo": [
            {
                "id": get_ip(device_id, host, token),
                "params": params,
                "type": "MANAGED_DEVICE_IP",
            }
        ],
        "templateId": template_id  
    }
    print(json.dumps(body, indent=2))

    url = "https://{}/dna/intent/api/v2/template-programmer/template/deploy".format(host)
    resp = requests.post(url, headers=headers, data=json.dumps(body), verify=False)
    print('task result: ' + json.dumps(resp.json()))

    task_id = resp.json()['response']['url']
    url = "https://{}{}".format(host, task_id)
    resp = requests.get(url, headers=headers, data=json.dumps(body), verify=False)
    print(resp.json())

    # Print deployment progress (usually done after 2 runs)
    count = 3
    while count > 0:
        time.sleep(5)
        resp = requests.get(url, headers=headers, data=json.dumps(body), verify=False)
        print(resp.json())
        count -= 1

# Get IP address for a device
def get_ip(device, host, token):
    headers = {
              'content-type': "application/json",
              'x-auth-token': token
          }

    url = "https://{}/dna/intent/api/v1/network-device/{}".format(host, device)
    resp = requests.get(url, headers=headers, verify=False)

    return resp.json()['response']['managementIpAddress']

# Get all GigabitEthernet ports for the given switch with their template status
def get_ports(switch, host, token):
    headers = {
              'content-type': "application/json",
              'x-auth-token': token
          }

    url = "https://{}/dna/intent/api/v1/interface/network-device/{}/{}/{}".format(host, switch, 1, 100)
    resp = requests.get(url, headers=headers, verify=False)
    ports = resp.json()['response']

    url = "https://{}/dna/intent/api/v1/network-device/{}/config".format(host, switch)
    resp = requests.get(url, headers=headers, verify=False)
    switch_config = resp.json()['response']
    with open('config.txt', 'w') as f:
        f.write(switch_config)

    result = []
    for p in ports:
        if p['portName'].startswith('GigabitEthernet'):
            new_p = p
            new_p['template'] = translate_template(find_template_for_interface(p['portName']))
            result += [new_p]
    return result

# Helper function
def get_id_for_template(name, host, token):
    templates = get_templates(host, token)
    for t in templates:
        if t['name'] == name:
            return t['id']

# Helper function
def translate_template(template):
    if template == "DefaultWiredDot1xClosedAuth":
        return "dot1X MAB"
    if template == "DefaultPrinter":
        return "Printer"
    if template == "DefaultCollaboration":
        return "Collaboration"

# Helper function
def find_template_for_interface(port):
    with open('config.txt', 'r') as f:
        reading = False
        for l in f.readlines():
            if l.strip() == f"interface {port}":
                reading = True
            if reading:
                if l.strip() == "!":
                    return None
                if "source template" in l:
                    return l.split(' ')[-1].strip()
        return None

# Get DNAC API token
def get_dnac_token(host, username, password):
    headers = {
              'content-type': "application/json",
              'x-auth-token': ""
          }

    url = "https://{}/api/system/v1/auth/token".format(host)
    response = requests.request("POST", url, auth=requests.auth.HTTPBasicAuth(username, password),
                                headers=headers, verify=False)
    return response.json()["Token"]