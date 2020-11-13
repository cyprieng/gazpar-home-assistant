# Gazpar home assistant

This module show your Gazpar consumption inside home assistant:
![Gazpar home assistant](https://user-images.githubusercontent.com/2521188/97164903-22fb9600-1783-11eb-9636-50f166eb47a0.png)

It is based on [empierre/domoticz_gaspar](https://github.com/empierre/domoticz_gaspar).


## Install

### HACS (recommended)

You can install this custom component using [HACS](https://hacs.xyz/) by adding a custom repository.

### Manual install

Copy this repository inside `config/custom_components/gazpar`.

## Configuration

Add this to your `configuration.yaml`:

```yaml
sensor:
  - platform: gazpar
    username: !secret gazpar.username
    password: !secret gazpar.password
    cost: 0.0539  # Cost per kWh
```

This will create 4 sensors:
* last day kWh
* last day EUR
* last month kWh
* last month EUR
 
