# VisionDesk systemd and Kiosk Setup

These commands assume the project is copied to `/home/pi/VisionDesk`.

## Reception Pi Backend Service

Run on `visiondesk-reception`:

```bash
sudo hostnamectl set-hostname visiondesk-reception
sudo cp /home/pi/VisionDesk/deployment/visiondesk.service /etc/systemd/system/visiondesk.service
sudo systemctl daemon-reload
sudo systemctl enable visiondesk.service
sudo systemctl start visiondesk.service
sudo systemctl status visiondesk.service
```

View logs:

```bash
journalctl -u visiondesk.service -f
```

## Reception Pi Kiosk

```bash
chmod +x /home/pi/VisionDesk/deployment/reception-kiosk.sh
mkdir -p /home/pi/.config/autostart
cp /home/pi/VisionDesk/deployment/kiosk-reception.desktop /home/pi/.config/autostart/
```

Reboot and the official 7 inch display will open:

```text
http://localhost:5000/reception
```

## Manual Desktop Icons

For a normal clickable desktop icon instead of forced kiosk mode:

```bash
chmod +x /home/pi/VisionDesk/deployment/start-visiondesk.sh
chmod +x /home/pi/VisionDesk/deployment/launch-reception-app.sh
cp /home/pi/VisionDesk/deployment/open-reception.desktop /home/pi/Desktop/
gio set /home/pi/Desktop/open-reception.desktop metadata::trusted true
chmod +x /home/pi/Desktop/open-reception.desktop
```

Double-click **VisionDesk Reception** to start the backend and open the web app.

## Manager Pi Kiosk

Run on `visiondesk-manager`:

```bash
sudo hostnamectl set-hostname visiondesk-manager
chmod +x /home/pi/VisionDesk/deployment/manager-kiosk.sh
mkdir -p /home/pi/.config/autostart
cp /home/pi/VisionDesk/deployment/kiosk-manager.desktop /home/pi/.config/autostart/
```

Reboot and Chromium will open:

```text
http://visiondesk-reception.local:5000/manager
```

For a normal manager desktop icon:

```bash
cp /home/pi/VisionDesk/deployment/open-manager.desktop /home/pi/Desktop/
gio set /home/pi/Desktop/open-manager.desktop metadata::trusted true
chmod +x /home/pi/Desktop/open-manager.desktop
```

## Network Check

From the manager Pi:

```bash
ping visiondesk-reception.local
curl http://visiondesk-reception.local:5000/api/health
```

If `.local` names do not resolve, install Avahi:

```bash
sudo apt install -y avahi-daemon
sudo systemctl enable avahi-daemon
sudo systemctl restart avahi-daemon
```
