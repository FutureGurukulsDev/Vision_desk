# RGB LED GPIO Setup

VisionDesk uses one RGB status LED on the reception Raspberry Pi.

## Default GPIO Pins

| LED Channel | GPIO Pin |
| --- | --- |
| Red | GPIO17 |
| Green | GPIO27 |
| Blue | GPIO22 |

Use suitable resistors for each LED channel. A common cathode RGB LED should connect the common leg to GND. A common anode LED requires inverted logic and should be adapted before deployment.

## Status Colors

| Color | Meaning |
| --- | --- |
| Blue | System Ready |
| Yellow | Waiting |
| Green | Approved |
| Red | Rejected |

## Environment Overrides

Set custom pins in `/etc/systemd/system/visiondesk.service`:

```ini
Environment=VISIONDESK_LED_RED_PIN=17
Environment=VISIONDESK_LED_GREEN_PIN=27
Environment=VISIONDESK_LED_BLUE_PIN=22
```

Disable LED support for development:

```bash
export VISIONDESK_LED_ENABLED=false
python app.py
```

## Test GPIO

```bash
python - <<'PY'
from gpiozero import RGBLED
from time import sleep

led = RGBLED(red=17, green=27, blue=22)
for color in [(0,0,1), (1,1,0), (0,1,0), (1,0,0)]:
    led.color = color
    sleep(1)
led.off()
PY
```
