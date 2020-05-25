# Integration Scripts
#
#          This script was developed by NetApp to help demonstrate NetApp
#          technologies.  This script is not officially supported as a
#          standard NetApp product.
#
# Purpose: Script to list all the checkpoints for a base partition, delete the last one and create a new one.
#
#
# Ejemplo de uso: >> listar_snaps_borrar_crear.py -v vol_name -apiuser admin -apipass password -a cluter_FQDN|(Mgmt:Port)
#
# Usage:   %> listar_snaps_borrar_crear.py <args>
#
# Author:  Dario Lopez (dariol@netapp.com) based on snap_show.py of Akshay Patil (akshay.patil@netapp.com)
#
# Se recuerda que este es un script de DEMO, que debe ser probado y ajustado al entorno productivo en el que se vaya a 
# ejecutar. La persona que ejecute este script asume TODA la responsabilidad de las operativas llevadas a cabo. 
# Ni NetApp ni el autor de este script asumen NINGUNA responsabilidad del uso que se le de al mismo. 
#
# NETAPP CONFIDENTIAL
# -------------------
# Copyright 2016 NetApp, Inc. All Rights Reserved.
#
# NOTICE: All information contained herein is, and remains the property
# of NetApp, Inc.  The intellectual and technical concepts contained
# herein are proprietary to NetApp, Inc. and its suppliers, if applicable,
# and may be covered by U.S. and Foreign Patents, patents in process, and are
# protected by trade secret or copyright law. Dissemination of this
# information or reproduction of this material is strictly forbidden unless
# permission is obtained from NetApp, Inc.
#
################################################################################
import base64
import argparse
import sys
import requests
import ssl
import subprocess
import time
from datetime import datetime
import os
from subprocess import call
import texttable as tt

global first_snap
global vol_uuid
requests.packages.urllib3.disable_warnings()

def count_snap(vol_name):
    #Contar snapshot identificado como mas antiguo
    tmp = dict(list_snaps(vol_name))
    count = tmp['result']['total_records']
    return count

def list_snaps(vol_name):
    #listar Snapshots del volumen en cuestion
    key=get_key(vol_name)
    global vol_uuid
    vol_uuid = key
    base64string = base64.encodestring('%s:%s' %(apiuser,apipass)).replace('\n', '')
    #print key
    url4= "https://{}/api/storage/volumes/{}/snapshots?fields=create_time,uuid&order_by=create_time".format(api,key)
    headers = {
        "Authorization": "Basic %s" % base64string,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    #print url4
    r = requests.get(url4,headers=headers,verify=False)
    #print r.json()
    return r.json()

def get_key(vol_name):
    #Obtener UUID del volumen en cuestion
    tmp = dict(get_volumes())
    vols = tmp['records']
    for i in vols:
        if i['name'] == vol_name:
            # print i
            return i['uuid']

def get_volumes():
    #Obtener listado de volumenes del cluster
    base64string = base64.encodestring('%s:%s' %(apiuser,apipass)).replace('\n', '')

    url = "https://{}/api/storage/volumes/".format(api)
    headers = {
        "Authorization": "Basic %s" % base64string,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    r = requests.get(url, headers=headers,verify=False)
    #print r.json()
    return r.json()

def disp_snaps(vol_name):
    #Mostrar snapshots entablados identificados con UUID y fecha de creacion
    #i = count_snap(vol_name)
    tmp = dict(list_snaps(vol_name))
    #print tmp
    snaps = tmp['records']
    tab = tt.Texttable()
    header = ['Snapshot name', 'Creation Time', 'Snapshot UUID']
    tab.header(header)
    tab.set_cols_align(['c','c','c'])
    global first_snap
    first_snap = snaps[0]['uuid']
    for i in snaps:
        ss = i['name']
        ss_uuid = i['uuid']
        s_b = i['create_time']
        row = [ss,s_b,ss_uuid]
        tab.add_row(row)
        tab.set_cols_align(['c','c','c'])
    s = tab.draw()
    print s


def delete_last_snap():
    #Borrar el snapshot identificado como mas antiguo
    base64string = base64.encodestring('%s:%s' % (apiuser, apipass)).replace('\n', '')
    print "https://{}/api/storage/volumes/{}/snapshots/{}?return_timeout=0".format(api,vol_uuid,first_snap)
    url4 = "https://{}/api/storage/volumes/{}/snapshots/{}?return_timeout=0".format(api,vol_uuid,first_snap)
    headers = {
        "Authorization": "Basic %s" % base64string,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    # print url4
    r = requests.delete(url4, headers=headers, verify=False)
    print r.json()
    #return r.json()
    disp_snaps(vol_name) #Lista de nuevo para comprobar

def create_snap():
    #Crear un nuevo snapshot del volumen
    base64string = base64.encodestring('%s:%s' % (apiuser, apipass)).replace('\n', '')
    print "https://{}/api/storage/volumes/{}/snapshots".format(api, vol_uuid)
    url4 = "https://{}/api/storage/volumes/{}/snapshots".format(api, vol_uuid)
    today = str(datetime.now())
    nombre = "API_Snap_"
    nombrado = nombre + today
    payload = {
        "name": nombrado
    }

    print nombrado
    headers = {
        "Authorization": "Basic %s" % base64string,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    # print url4
    r = requests.post(url4, headers=headers, json=payload, verify=False)
    print r.json()
    # return r.json()
    disp_snaps(vol_name)  # Lista de nuevo para comprobar

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Passing variables to the program')
    parser.add_argument('-v','--vol_name', help='Volume to list snapshots of',dest='vol_name',required=True)
    parser.add_argument('-a','--api', help='API server IP:port details',dest='api')
    parser.add_argument('-apiuser','--apiuser', help='Add APIServer Username',dest='apiuser',required=True)
    parser.add_argument('-apipass','--apipass', help='Add APIServer Password',dest='apipass',required=True)
    globals().update(vars(parser.parse_args()))
    #print "Total number of snapshots for the volume {} = {}".format(vol_name)
    print "DISCLAIMER -> Utilice el script estando seguro de la operativa a realizar, no hay WARNINGS, no 'Crtl-Z' posible"
    disp_snaps(vol_name)
    print "El snapshot mas antiguo que sera borrado tiene UUID: {} ".format(first_snap)
    print "Desea borrar el snapshot indicado (No vuelta atras)"
    while 1:
        a = raw_input("Enter yes/no to continue: ").lower()
        if a == "yes" or a == "y":
            print "Borrando.."
            delete_last_snap()
            break
        elif a == "no" or a == "n":
            print "Elegiste NO. Saliendo.. "
            break
        else:
            print("Please, enter either yes/no...")

    #Tomar nuevo snapshot:
    print "Desea ejecutar un Snapshot en este momento para el volumen {}".format(vol_name)
    while 1:
        a = raw_input("Enter yes/no to continue: ").lower()
        if a == "yes" or a == "y":
            print
            "Creando Snapshot.."
            create_snap()
            break
        elif a == "no" or a == "n":
            print
            "Elegiste NO. Saliendo.. "
            break
        else:
            print("Please, enter either yes/no...")