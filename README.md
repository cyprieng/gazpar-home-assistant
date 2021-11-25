# Gazpar home assistant

This module show your Gazpar consumption inside home assistant.


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
    pce: 1234567890  # PCE identifier (can be found on grdf.fr)
```

This will create a kwh index sensor that can be used in HA energy.
 
