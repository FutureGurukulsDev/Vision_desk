"""RGB status LED service.

The service uses gpiozero on Raspberry Pi hardware and silently falls back to a
no-op software mode on development machines.
"""

from flask import current_app


class LedService:
    """Controls the reception RGB LED state."""

    def __init__(self) -> None:
        self._led = None
        self._available = False

    def initialize(self) -> None:
        """Initialize GPIO pins when LED support is enabled."""
        if self._available or not current_app.config.get("LED_ENABLED", True):
            return

        try:
            from gpiozero import RGBLED
        except ImportError:
            current_app.logger.warning("gpiozero not installed; LED service disabled.")
            return

        self._led = RGBLED(
            red=current_app.config["LED_RED_PIN"],
            green=current_app.config["LED_GREEN_PIN"],
            blue=current_app.config["LED_BLUE_PIN"],
            active_high=True,
        )
        self._available = True

    def set_color(self, color: str) -> None:
        """Set the RGB LED to a named workflow color."""
        self.initialize()
        colors = {
            "blue": (0, 0, 1),
            "yellow": (1, 1, 0),
            "green": (0, 1, 0),
            "red": (1, 0, 0),
            "off": (0, 0, 0),
        }
        if self._available and self._led:
            self._led.color = colors.get(color, colors["off"])

    def set_ready(self) -> None:
        """Show system ready state."""
        self.set_color("blue")

    def set_waiting(self) -> None:
        """Show visitor waiting state."""
        self.set_color("yellow")

    def set_approved(self) -> None:
        """Show visitor approved state."""
        self.set_color("green")

    def set_rejected(self) -> None:
        """Show visitor rejected state."""
        self.set_color("red")


led_service = LedService()
