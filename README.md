# Gazpar home assistant

This module show your Gazpar consumption inside home assistant:
![Gazpar home assistant](https://user-images.githubusercontent.com/2521188/97164903-22fb9600-1783-11eb-9636-50f166eb47a0.png)

It is based on [empierre/domoticz_gaspar](https://github.com/empierre/domoticz_gaspar).

## Getting started

Copy this repository inside `config/custom_components/gazpar`.

Add this to your `configuration.yaml`:

```yaml
sensor:
  - platform: gazpar
    username: !secret gazpar.username
    password: !secret gazpar.password
    cost: 0.0539  # Cost per kWh
```

This will create 4 sensors:
* last day kWH
* last day EUR
* last month kWH
* last month EUR
 
