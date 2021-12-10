#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import requests
import urllib3
import time
from requests.auth import HTTPBasicAuth
from pprint import pprint
from genie.conf.base import Device
import numpy as np
import matplotlib.pyplot as plt

# https://sandboxdnac.cisco.com/
DNAC_HOST = "sandboxdnac.cisco.com"
DNAC_USER = "devnetuser"
DNAC_PASS = "Cisco123!"
DNAC_DEVICE_HOSTNAME = "leaf1.abc.inc"
DNAC_TIMEOUT = 0

# Silence the insecure warning due to SSL Certificate
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class dnacApiClass:
    def __init__(self):
        pass

    def auth(self, dnacHost, dnacUser, dnacPass):
        # --------------------------------------------------------------------------------
        # Authentication API
        # https://developer.cisco.com/docs/dna-center/#!cisco-dna-center-2-1-2-x-api-api-authentication-authentication-api
        # --------------------------------------------------------------------------------
        url = "https://"+dnacHost+"/api/system/v1/auth/token"
        headers = {
            'Content-Type': "application/json",
            }
        payload = ""
        response = requests.post(url, auth = HTTPBasicAuth(dnacUser, dnacPass), headers = headers, data = payload, verify = False)
        if response.status_code == 200:
            dnacToken = json.loads(response.text)
            dnacToken = dnacToken["Token"]
            return(dnacToken)
        else:
            print(">>> Error Cisco DNA-C 'Auth' Failed <<<")
            print("HTTP response status code : {}".format(response.status_code))
            return False

    def get_all_device_id(self, dnacToken):
        # --------------------------------------------------------------------------------
        # Get Device List
        # https://developer.cisco.com/docs/dna-center/#!cisco-dna-center-2-1-2-x-api-api-devices-get-device-list
        # --------------------------------------------------------------------------------
        url = "https://{}/api/v1/network-device".format(DNAC_HOST)
        headers = {
            'x-auth-token': dnacToken,
            'Content-Type': "application/json",
            'Accept': "application/json"
            }
        all_device_response = requests.get(url, headers = headers, verify = False)
        device_list = all_device_response.json()
        for device in device_list['response']:
            print("DEBUG : Hostname = [{}] , id = [{}]".format(device['hostname'], device['id']))

    def get_device_id_from_hostname(self, device_name, dnacToken):
        # --------------------------------------------------------------------------------
        # Get Device List
        # https://developer.cisco.com/docs/dna-center/#!cisco-dna-center-2-1-2-x-api-api-devices-get-device-list
        # --------------------------------------------------------------------------------
        url = "https://{}/api/v1/network-device".format(DNAC_HOST)
        headers = {
            'x-auth-token': dnacToken,
            'Content-Type': "application/json",
            'Accept': "application/json"
            }
        all_device_response = requests.get(url, headers = headers, verify = False)
        device_list = all_device_response.json()
        for device in device_list['response']:
            # For the purpose of debugging.
            # print("DEBUG : Hostname = [{}] , id = [{}]").format((device)['hostname'], (device)['id'])
            # print(device)
            if device['hostname'] == device_name:
                return device['id']
        print(">>> Error Cisco DNA-C 'Hostname was not found.' <<<")
        return False

    def run_command_and_get_task_id(self, deviceId, deviceCmd, dnacToken):
        # --------------------------------------------------------------------------------
        # Run Read Only Commands On Devices To Get Their Real Time Configuration
        # https://developer.cisco.com/docs/dna-center/#!cisco-dna-center-2-1-2-x-api-api-command-runner-run-read-only-commands-on-devices-to-get-their-real-time-configuration
        # --------------------------------------------------------------------------------
        url = "https://{}/api/v1/network-device-poller/cli/read-request".format(DNAC_HOST)
        headers = {
            'x-auth-token': dnacToken,
            'Content-Type': "application/json",
            'Accept': "application/json"
            }
        payload = {
            "commands": [deviceCmd],
            "deviceUuids": [deviceId],
            "timeout": DNAC_TIMEOUT
            }
        response = requests.post(url, headers = headers, data = json.dumps(payload), verify = False)
        response_json = response.json()
        try:
            task_id = response_json['response']['taskId']
            return task_id
        except:
            print(">>> Error Cisco DNA-C 'Run Read Only Commands' Failed <<<")
            return False

    def get_file_id(self, taskId, dnacToken):
        # --------------------------------------------------------------------------------
        # Get Tasks
        # https://developer.cisco.com/docs/dna-center/#!cisco-dna-center-2-1-2-x-api-api-task-get-tasks
        # --------------------------------------------------------------------------------
        url = "https://{}/api/v1/task/{}".format(DNAC_HOST, taskId)
        headers = {
            'x-auth-token': dnacToken,
            'Content-Type': "application/json",
            'Accept': "application/json"
            }
        while True:
            try:
                task_response = requests.get(url, headers = headers, verify = False)
                task_json = task_response.json()
                file_info = json.loads(task_json['response']['progress'])
                file_id = file_info['fileId']
                return file_id
            except:
                if task_json['response']['isError'] is True:
                    print(">>> Error Cisco DNA-C 'Get Task' Failed <<<")
                    return False
                pass
            finally:
                time.sleep(1)

    def download_file(self, fileId, deviceCmd, dnacToken):
        # --------------------------------------------------------------------------------
        # Download A File By File Id
        # https://developer.cisco.com/docs/dna-center/#!cisco-dna-center-2-1-2-x-api-api-file-download-a-file-by-file-id
        # --------------------------------------------------------------------------------
        url_file = "https://{}/api/v1/file/{}".format(DNAC_HOST, fileId)
        headers = {
            'x-auth-token': dnacToken,
            'Content-Type': "application/json",
            'Accept': "application/json"
            }
        response = requests.get(url_file, headers = headers, verify = False, stream = True)
        response_json = response.json()
        try:
            command_response = response_json[0]['commandResponses']['SUCCESS'][deviceCmd]
        except:
            command_response = response_json[0]['commandResponses']['FAILURE'][deviceCmd]
            print(">>> Error Cisco DNA-C 'Download File' Failed <<<")
            print(command_response)
            return False
        return command_response


if __name__ == '__main__':
    dnacApi = dnacApiClass()

    # >>> Get a token to access DNAC. <<<
    dnacToken = dnacApi.auth(DNAC_HOST, DNAC_USER, DNAC_PASS)
    if dnacToken is False:
        quit()

    # >>> Display all hostnames and device IDs (for debugging) <<<
    dnacApi.get_all_device_id(dnacToken)

    # >>> Search for Device ID from the host name and get it. <<<
    deviceId = dnacApi.get_device_id_from_hostname(DNAC_DEVICE_HOSTNAME, dnacToken)
    if deviceId is False:
        quit()

    # >>> Run show interfaces command and get the Task ID <<<
    DNAC_CMD =  "show interfaces"
    taskId = dnacApi.run_command_and_get_task_id(deviceId, DNAC_CMD, dnacToken)
    if taskId is False:
        quit()
    fileId = dnacApi.get_file_id(taskId, dnacToken)
    if fileId is False:
        quit()
    result_cmd = dnacApi.download_file(fileId, DNAC_CMD, dnacToken)
    if result_cmd is False:
        quit()
    print(result_cmd)

    # >>> Genie parses the output results of the command and converts them to JSON. <<<
    try:
        device = Device(DNAC_DEVICE_HOSTNAME, os='iosxe')
        device.custom.setdefault("abstraction", {})["order"] = ["os"]
        result_json = device.parse(DNAC_CMD, output=result_cmd)
    except:
        print(">>> Error Genie parser Failed <<<")
        print(sys.exc_info())
        quit()
    pprint(result_json)

    # >>> Extract only the UP/UP interfaces from the results of show interfaces and add them to the list. <<<
    up_interfaces = []
    for temp_interface in result_json:
        if result_json[temp_interface]['line_protocol'] == 'up' and result_json[temp_interface]['oper_status'] == 'up':
            up_interfaces.append(temp_interface)

    # >>> Run show interface stats command and get the Task ID <<<
    DNAC_CMD =  "show interface stats"
    taskId = dnacApi.run_command_and_get_task_id(deviceId, DNAC_CMD, dnacToken)
    if taskId is False:
        quit()
    fileId = dnacApi.get_file_id(taskId, dnacToken)
    if fileId is False:
        quit()
    result_cmd = dnacApi.download_file(fileId, DNAC_CMD, dnacToken)
    if result_cmd is False:
        quit()
    print(result_cmd)

    # >>> Genie parses the output results of the command and converts them to JSON. <<<
    try:
        device = Device(DNAC_DEVICE_HOSTNAME, os='iosxe')
        device.custom.setdefault("abstraction", {})["order"] = ["os"]
        result_json = device.parse(DNAC_CMD, output=result_cmd)
    except:
        print(">>> Error Genie parser Failed <<<")
        print(sys.exc_info())
        quit()
    pprint(result_json)

    # >>> Retrieve and save stats information as a reference (initial value). <<<
    base_counter = []
    for temp_interface in result_json:
        if temp_interface in up_interfaces:
            temp_list = []
            temp_list.append(temp_interface)
            temp_list.append(result_json[temp_interface]['switching_path']['total']['pkts_in'])
            temp_list.append(result_json[temp_interface]['switching_path']['total']['pkts_out'])
            base_counter.append(temp_list)

    # >>> Create a Figure object as a drawing area in Matplotlib. <<<
    fig = plt.figure(tight_layout=True)

    # >>> Create the same number of subplots as the number of interfaces that are UP/UP. <<<
    axes = fig.subplots(len(up_interfaces),1)
    
    # >>> Set the interface names as the title for each subplot. <<<
    for i in range(0, len(up_interfaces)):
        axes[i].set_title(up_interfaces[i])
 
    # >>> Update the graph 30 times and quit. <<<
    for i_loop in range(0,30):

        # >>> Run show interface stats command and get the Task ID <<<
        DNAC_CMD =  "show interface stats"
        taskId = dnacApi.run_command_and_get_task_id(deviceId, DNAC_CMD, dnacToken)
        if taskId is False:
            quit()
        fileId = dnacApi.get_file_id(taskId, dnacToken)
        if fileId is False:
            quit()
        result_cmd = dnacApi.download_file(fileId, DNAC_CMD, dnacToken)
        if result_cmd is False:
            quit()
        print(result_cmd)

        # >>> Genie parses the output results of the command and converts them to JSON. <<<
        try:
            device = Device(DNAC_DEVICE_HOSTNAME, os='iosxe')
            device.custom.setdefault("abstraction", {})["order"] = ["os"]
            result_json = device.parse(DNAC_CMD, output=result_cmd)
        except:
            print(">>> Error Genie parser Failed <<<")
            print(sys.exc_info())
            quit()
        pprint(result_json)

        # >>> Get and save the latest stats information. <<<
        latest_counter = []
        for temp_interface in result_json:
            if temp_interface in up_interfaces:
                temp_list = []
                temp_list.append(temp_interface)
                temp_list.append(result_json[temp_interface]['switching_path']['total']['pkts_in'])
                temp_list.append(result_json[temp_interface]['switching_path']['total']['pkts_out'])
                latest_counter.append(temp_list)

        # >>> Draw a graph comparing the initial stats with the latest stats information. <<<
        for i in range(0, len(up_interfaces)):
            diff_total_in = int(latest_counter[i][1]) - int(base_counter[i][1])
            diff_total_out = int(latest_counter[i][2]) - int(base_counter[i][2])
            height = np.array([diff_total_out, diff_total_in])
            height_max = max([diff_total_out, diff_total_in])

            # >>> If the width of the bar chart exceeds 100, specify that value as the maximum bar chart width. <<<
            if height_max >= 100:
                axes[i].set_xlim(0, height_max)
            else:
                # >>> If the width of the bar chart does not exceed 100, specify 100 as the maximum bar chart width. <<<
                axes[i].set_xlim(0, 100)
            x_bar = np.array(["Total Pkts Out", "Total Pkts In"])
            axes[i].barh(x_bar, height, color=['#aa4c8f','#1e50a2'], edgecolor=['r','b'])

        # >>> Display the graph and wait for the specified time. <<<
        plt.pause(0.1)

    # >>> Close the graph window if you want to quit the script because it stops with the last graph displayed. <<<
    plt.show()