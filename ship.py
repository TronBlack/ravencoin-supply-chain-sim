#!/usr/bin/env python3
# Simulation of a supply-chain.  Send assets (representing goods), with manifest info
# Reads addresses from <ip>.addresses.json in the same folder for addresses

#If you need pip
#    sudo easy_install pip

#If you need tinydb
#    sudo pip install tinydb

#If you need ipfs
#   1. Get IPFS - https://ipfs.io/
#   2. Run the ipfs daemon
#   3. pip install ipfsapi

import subprocess
import json
from datetime import datetime
import random
from tinydb import TinyDB, Query
from tinydb.operations import set
import socket
import time
import os

#Set this to your raven-cli program
cli = "raven-cli"

mode =  "-testnet"
rpc_port = 18766
#mode =  "-regtest"
#rpc_port = 18443

asset="TRACKEDGOODS"
extension=".addresses.json"

#Set this information in your raven.conf file (in datadir, not testnet3)
rpc_user = 'rpcuser'
rpc_pass = 'rpcpass555'

if os.name != "nt":
    import fcntl
    import struct

    def get_interface_ip(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s',
                                ifname[:15]))[20:24])

def get_lan_ip():
    ip = socket.gethostbyname(socket.gethostname())
    if ip.startswith("127.") and os.name != "nt":
        interfaces = [
            "eth0",
            "eth1",
            "eth2",
            "wlan0",
            "wlan1",
            "wifi0",
            "ath0",
            "ath1",
            "ppp0",
            ]
        for ifname in interfaces:
            try:
                ip = get_interface_ip(ifname)
                break
            except IOError:
                pass
    return ip


def get_rpc_connection():
    from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
    connection = "http://%s:%s@127.0.0.1:%s"%(rpc_user, rpc_pass, rpc_port)
    #print("Connection: " + connection)
    rpc_conn = AuthServiceProxy(connection)
    return(rpc_conn)
    
rpc_connection = get_rpc_connection()

def listmyassets(filter):
    result = rpc_connection.listmyassets(filter)
    print result
    return(result) 

def getaddressesbyaccount(account):
    result = rpc_connection.getaddressesbyaccount(account)
    return(result) 

def rpc_call(params):
    process = subprocess.Popen([cli, mode, params], stdout=subprocess.PIPE)
    out, err = process.communicate()
    return(out)

def generate_blocks(n):
    hashes = rpc_connection.generate(n)
    return(hashes)

def transfer(asset, qty, address, memo_hash='', memo_expiration=0, change_address=''):
    result = rpc_connection.transfer(asset, qty, address, memo_hash, memo_expiration, change_address)  #This should change if we move change address to the end
    return(result)

def share_my_addresses(fname):
    db = TinyDB(fname)
    Addresses = Query()
    addresses = getaddressesbyaccount("")
    count = len(addresses)
    print("Adding " + str(count) + " addresses.")
    count = 0
    for address in addresses:
        if count < 10:
            db.upsert({'address': address}, Addresses.address == address)
            count = count + 1

def get_address_files():
    import os
    files = []
    for file in os.listdir("."):
        if file.endswith(extension):
            files.append(file)
    return(files)

def create_master_list_of_addresses():
    Addresses = Query()
    files = get_address_files()
    address_list = []
    fname = get_our_db_file()
    #Loop through all the files and create a master list
    for file in files:
        if file != fname:
            db = TinyDB(file)
            addresses = db.search(Addresses.address != "")
            for address in addresses:
                address_list.append(address['address'])
    #print(result)
    print("Num addresses: " + str(len(address_list)))
    return(address_list)

def get_others_address(master_address_list):
    import random

    if (len(master_address_list) == 0):
        print("You must include address files from other nodes.\nExpected format <ip>"+extension)
        exit(-1)        

    #Choose an address from the master list
    selected = random.randint(0, len(master_address_list)-1)
    return(master_address_list[selected])

def transfer_asset(asset, qty, address, memo=None, memo_expiration=0, change_address=''):
    #Add the message to IPFS

    memo_hash = None
    if memo is not None:
        memo_hash = add_memo(memo)

    result = transfer(asset, qty, address, memo_hash, memo_expiration, change_address)
    return(result[0])

def add_to_ipfs(json_str):
    print("Adding to IPFS")
    import ipfsapi
    api = ipfsapi.connect('127.0.0.1', 5001)
    res = api.add_str(json_str)
    print(res)
    print("Printed res")
    return(res)


#TODO Add memo to IPFS and return memo_hash 
def add_memo(json_str):
    #print("Adding memo to ipfs")
    memo_hash = add_to_ipfs(json_str)
    #print("Added memo to ipfs")
    #print(memo_hash)
    return memo_hash

def create_address_file():
    import os
    fname = get_our_db_file()
    if not os.path.isfile(fname):
        print("Filename " + fname + " not found.  Creating...") 
        share_my_addresses(fname)

def get_our_db_file():
    import os.path
    #ip = socket.gethostbyname(socket.gethostname())
    ip = get_lan_ip()
    fname = ip + extension
    return(fname)

def fission(master_address_list, filter):
    transferred = 0
    while (True):
        assets = listmyassets(filter)
        print("Fission asset count: " + str(len(assets)))
        for asset, qty in assets.items():
            if not asset.endswith('!'):  #Only send if not admin token
                address1 = get_others_address(master_address_list)
                address2 = get_others_address(master_address_list)
                if (qty > 1):
                    qty1 = int(qty / 2)
                else:
                    qty1 = qty

                qty2 = qty - qty1
                print("Transfer " + asset + " Qty:" + str(qty1) + " to " + address1)
                try:
                    txid1 = transfer_asset(asset, qty1, address1)
                    print("TxId 1: " + txid1)
                    transferred=transferred+1
                    print("Asset transfer count: " + str(transferred))
                except BaseException as err:
                    print("Could not send asset " + asset + ". Possibly already sent, waiting for confirmation.")
                    print(err)
                
                print("Transfer " + asset + " Qty:" + str(qty2) + " to " + address1)
                try:
                    txid2 = transfer_asset(asset, qty2, address2)
                    print("TxId 2: " + txid2)
                    transferred=transferred+1
                    print("Asset transfer count: " + str(transferred))
                except BaseException as err:
                    print("Could not send asset " + asset + ". Possibly already sent, waiting for confirmation.")
                    print(err)

                print("")
        time.sleep(60)

def get_random_carrier():
    with open('carrier_list.json') as json_file:  
        carriers = json.load(json_file)
    a_count = len(carriers)
    r = random.randint(0,len(carriers)-1)
    return(carriers[r])

def get_random_tracking():
    letter = chr(random.randint(65, 65+25))
    length = random.randint(6, 24)
    tracking = letter
    for x in range(length):
        tracking += str(random.randint(0,9))
    return(tracking)

def get_random_location():
    r = random.randint(0,len(shipping_addresses['addresses'])-1)
    return(shipping_addresses['addresses'][r])


def get_random_insurer():
    with open('insurer_list.json') as json_file:  
        insurers = json.load(json_file)
    r = random.randint(0,len(insurers)-1)
    return(insurers[r])

def get_time():
    return(datetime.today().strftime('%Y-%m-%d %H:%M:%S'))

def read_shipping_addresses():
    with open('addresses.json') as json_file:  
        s_add = json.load(json_file)
    return(s_add)

#Returns a JSON object
def build_bill_of_lading(prev_bill_of_lading = None):
    data = {}
    data['loaded'] = get_time()
    data['carrier'] = get_random_carrier()
    data['tracking'] = get_random_tracking()
    
    if prev_bill_of_lading is None:
        data['insurer'] = get_random_insurer()
        data['from'] = get_random_location()
    else:
        data['insurer'] = prev_bill_of_lading['insurer']
        data['from'] = prev_bill_of_lading['to']

    data['to'] = get_random_location()
    return(data)

def ship(master_address_list, filter):
    transferred = 0
    #while (True):
    while (transferred < 1):   #Temporary to transfer one asset
        assets = listmyassets(filter)
        print("Goods asset count: " + str(len(assets)))
        for asset, qty in assets.items():
            qty = 1 #TODO - temporary overide of qty to 1
            if not asset.endswith('!'):  #Only send if not admin token
                address = get_others_address(master_address_list)
                print("Ship " + asset + " Qty:" + str(qty) + " to " + address)
                try:
                    bol = build_bill_of_lading()
                    txid = transfer_asset(asset, qty, address, json.dumps(bol))
                    print("TxId: " + txid)
                    transferred=transferred+1
                    print("Shipping count: " + str(transferred))
                except BaseException as err:# JSONRPCException:
                    print("Could not send asset " + asset + ". Possibly already sent, waiting for confirmation.")
                    print(err)
                print("")
        time.sleep(1)



if mode == "-regtest":  #If regtest then mine our own blocks
    import os
    os.system(cli + " " + mode + " generate 400")


create_address_file()
master_list = create_master_list_of_addresses()
shipping_addresses = read_shipping_addresses()
ship(master_list, asset)  #Set to "*" for all.
