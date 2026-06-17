# Home Assistant Automations

Here are some example automations you can use with the Gmail Parcels integration.

## Sensors

The integration exposes a matrix of **count** sensors (no per-parcel entities).
All counts come from the addon; rich detail (status history, photos) lives in the
addon's WebUI / REST API, not in HA attributes.

**Global:**
- `sensor.parcels_upcoming`: parcels on the way (everything not delivered).
- `sensor.parcels_today`: parcels expected today (out-for-delivery or ETA today).
- `sensor.parcels_delivered`: delivered parcels still tracked (last 7 days).

**Per carrier** (`ups`, `fedex`, `usps`, `dhl`, plus `other` for unmodeled carriers):
- `sensor.parcels_<carrier>`: active (upcoming) parcels for that carrier.
- `sensor.parcels_<carrier>_upcoming` / `_today` / `_delivered`: per-bucket counts.

The global sensors and each `sensor.parcels_<carrier>` total carry a lean
`parcels` attribute list — `tracking`, `carrier`, `status`, `eta`, `sender`,
`updated` (deliberately no history or photo paths). The `_<bucket>` count sensors
are pure counts to keep the recorder light.

## Examples

### 1. Notify when a parcel is out for delivery

This automation sends a notification to your phone when the "Parcels Arriving Today" count increases.

```yaml
alias: "Parcel Out for Delivery"
description: "Notify when a parcel is expected today"
trigger:
  - platform: state
    entity_id: sensor.parcels_today
    from: null
condition:
  - condition: template
    value_template: "{{ trigger.to_state.state | int > trigger.from_state.state | int }}"
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "📦 Parcel Arriving Today!"
      message: >
        You have {{ states('sensor.parcels_today') }} parcel(s) scheduled for delivery today.
        
        {% for parcel in state_attr('sensor.parcels_today', 'parcels') %}
        - {{ parcel.carrier }}: {{ parcel.status }}
        {% endfor %}
```

### 2. Notify when a parcel is delivered

This automation triggers when the delivered count goes up.

```yaml
alias: "Parcel Delivered"
description: "Notify when a parcel status changes to delivered"
trigger:
  - platform: state
    entity_id: sensor.parcels_delivered
    from: null
condition:
  - condition: template
    value_template: "{{ trigger.to_state.state | int > trigger.from_state.state | int }}"
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "📬 Parcel Delivered"
      message: "A parcel has just been delivered! Check your mailbox."
```

### 3. Morning Briefing

Send a summary of incoming packages every morning at 8:00 AM.

```yaml
alias: "Morning Parcel Briefing"
trigger:
  - platform: time
    at: "08:00:00"
condition:
  - condition: numeric_state
    entity_id: sensor.parcels_upcoming
    above: 0
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "Daily Parcel Update"
      message: >
        Good morning! 
        
        You have {{ states('sensor.parcels_upcoming') }} parcel(s) on the way.
        {{ states('sensor.parcels_today') }} of them are arriving today.
```

### 4. Dashboard Card

You can use the Markdown card in your Lovelace dashboard to show a list of parcels.

```yaml
type: markdown
content: >
  ## 📦 Incoming Parcels

  {% set parcels = state_attr('sensor.parcels_upcoming', 'parcels') %}
  {% if parcels %}
    {% for p in parcels %}
    **{{ p.carrier }}** ({{ p.tracking }})
    Status: {{ p.status }}
    {% if p.eta %}ETA: {{ p.eta }}{% endif %}
    ---
    {% endfor %}
  {% else %}
    No upcoming parcels.
  {% endif %}
title: Parcels
```
