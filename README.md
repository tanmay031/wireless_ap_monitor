
# Wireless AP Monitor System

## Task Statement

This project consists of two Python applications (app_A and app_B) that monitor and communicate changes in wireless access points (APs) through RabbitMQ. app_A tracks changes in a JSON file representing APs and sends notifications about additions, removals, and changes in SNR or channel to multiple instances of app_B, which display these changes.

## Overview
### Fatures:
- Monitor Changes: app_A monitors changes in a JSON file (access_points.json), including:
  - AP is added or removed.
  - SNR or channel value has changed.
- Notifications: Detected changes are sent to app_B instances via RabbitMQ using a fanout exchange.
- Multiple Consumers: You can run multiple instances of app_B, and each will receive and display the notifications.

### Example Scenario

Given the following JSON structure:
```json
{
  "access_points": [
    {
      "ssid": "MyAP",
      "snr": 63,
      "channel": 11
    },
    {
      "ssid": "YourAP",
      "snr": 42,
      "channel": 1
    }
  ]
}
```
When the file changes to:
```json
{
  "access_points": [
    {
      "ssid": "MyAP",
      "snr": 82,
      "channel": 11
    },
    {
      "ssid": "YourAP",
      "snr": 42,
      "channel": 6
    },
    {
      "ssid": "HerAP",
      "snr": 71,
      "channel": 1
    }
  ]
}
```

The output would be:
```
MyAP’s SNR has changed from 63 to 82
YourAP’s channel has changed from 1 to 6
HerAP is added to the list with SNR 71 and channel 1
```


## Requirements

- **Docker** and **Docker Compose**
- **Python 3.9+** (if not using Docker)
- **RabbitMQ** (installed in Docker)

## Setup and Running the Applications

### 1. Clone the Repository
```bash
git clone https://github.com/tanmay031/wireless_ap_monitor.git
cd wireless_ap_monitor
```

### 2. Set Up Environment Variables
Create a `.env` file in the project root with the following content to configure RabbitMQ:
```bash
RABBITMQ_USER=user
RABBITMQ_PASSWORD=password
RABBITMQ_SERVER=rabbitmq
```

### 3. Build and Run the Services with Docker Compose
To build and run the services, use:
```bash
docker-compose up --build
```

This will:
- Start RabbitMQ on ports 5672 (AMQP) and 15672 (management UI).
- Start app_A to monitor changes in the access_points.json file.
- Start three instances of app_B, each listening for updates.

### 4. Modify the `access_points.json` File
To simulate AP changes, modify the `access_points.json` file. You can add, remove, or update APs' SNR and channel.

For example, modifying:
```json
{
  "access_points": [
    {
      "ssid": "MyAP",
      "snr": 63,
      "channel": 11
    }
  ]
}
```
to:
```json
{
  "access_points": [
    {
      "ssid": "MyAP",
      "snr": 82,
      "channel": 11
    },
    {
      "ssid": "NewAP",
      "snr": 70,
      "channel": 3
    }
  ]
}
```
Will result in `app_B` instances logging:
```
MyAP’s SNR has changed from 63 to 82
NewAP is added to the list with SNR 70 and channel 3
```

### 3. Stop the Services
To stop all services, use:
```bash
docker-compose down
```

