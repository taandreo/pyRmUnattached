from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from datetime import datetime, timedelta
import azure.functions as func
import logging
import re
import json

FORMAT = "%(asctime)s: %(message)s"
logging.basicConfig(format=FORMAT, level=logging.WARNING)

def main(mytimer: func.TimerRequest) -> None:
    try:
        file = open('pyRmUnattached/data.json', "r")
        data = json.load(file)
        subscriptions = data['subscriptions']
        patterns = data['ignore_patterns']
        retention_days = data['retention_days']
    except:
        logging.error("Error: Error getting information from data.json file.")
        exit(1)

    if subscriptions == []:
        logging.error("Error: No subscription found in data.json file.")
        exit(1)

    for subscription_id in subscriptions:
        logging.warning(f"Connecting in susbcription {subscription_id} ..." )
        credential = DefaultAzureCredential(exclude_visual_studio_code_credential=True, exclude_environment_credential=True)
        cp_client = ComputeManagementClient(credential, subscription_id)

        logging.warning(f"Getting disk list for subscription {subscription_id}")
        disks = cp_client.disks.list()

        remove_list = []
        for disk in disks:
            if exception_disks(disk.name, patterns):
                if disk.managed_by == None and disk.disk_state == "Unattached":
                    logging.warning(f"Unattached disk found: {disk.name}")
                    disk = add_tag(disk, cp_client)
                    remove_date = check_remove(retention_days, disk)
                    if remove_date:
                        logging.warning(f"Adding disk {disk.name} for remove. Remove date: {remove_date}")
                        remove_list.append(disk)      
                        
        if remove_list:
            logging.warning(f"Removing disks older then {retention_days} days.")
            for disk in remove_list:
                #logging.warning(f"Removing disk {disk.name} ...")
                remove_disk(disk, cp_client)
        else:
            logging.warning("No disks found for remove")
    
    file.close()
    

def check_remove(days: int, disk):
    now = datetime.now()
    iso_date = disk.tags.get("unattached_time")
    
    disk_date = datetime.fromisoformat(iso_date) 
    remove_date = disk_date + timedelta(days=days)
    
    if remove_date < now:
        return remove_date
    
    return None

def remove_disk(disk, client):
    name = disk.name
    rg = disk.id.split("/")[4]
    client.disks.begin_delete(rg, name)
    logging.warning(f"Remove command sent to disk {name}.")

def exception_disks(disk_name: str, patterns):
    if patterns == []:
        return True
    for pattern in patterns:
        if re.search(pattern, disk_name):
            logging.warning(f"by pass to disk {disk_name}")
            return False
        else:
            return True

def add_tag(disk, client):
    now = datetime.now()
    name = disk.name
    rg = disk.id.split("/")[4]
    
    if disk.tags == None:
        logging.warning(f"Adding tag for {name} ...")
        disk.tags = {'unattached_time': now.isoformat()}
        client.disks.begin_update(rg, name, disk)
    elif disk.tags.get('unattached_time'):
        pass
    else:
        logging.warning(f"Adding tag for {name} ...")
        disk.tags["unattached_time"] = now.isoformat()
        client.disks.begin_update(rg, name, disk)
    
    return disk

if __name__ == "__main__":
    main()