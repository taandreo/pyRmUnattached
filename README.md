# pyRmUnattached

Function to remove unattached disks in Azure.

## pyRmUnattached/data.json

Defines some configuration parameters that change the execution of the function.
```json
{
    "subscriptions": [
        "subscription_id"
    ],
    "ignore_patterns": [
        "regex-(disk_name)"
    ],
    "retention_days": 2
}
```

`subscriptions`: What subscription this function will run.  
`ignore_patterns`: Disk name pattern that will be exclude from the execution. Need to be a regex.  
`retention_days`: Retention time for the unttached disks. Disks with more than "x" days will be removed.  

## pyRmUnattached/function.json
```json
{
  "scriptFile": "main.py",
  "bindings": [
    {
      "name": "mytimer",
      "type": "timerTrigger",
      "direction": "in",
      "schedule": "0 22 * * * *"
    }
  ]
}
```

The indicated schedule for the function is that it runs daily, as configured in the json above.
