# app_a/app_a.py
import json
import time
import os
import pika
import logging

# File path to monitor (located in the current directory inside the container)
FILE_PATH = './access_points.json'

# RabbitMQ server details
RABBITMQ_SERVER = os.getenv('RABBITMQ_SERVER', 'rabbitmq')
EXCHANGE_NAME = 'ap_changes'
EXCHANGE_TYPE = 'fanout'  # 'fanout' exchange broadcasts messages to all queues

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_access_points(file_path):
    """Load access points data from a JSON file."""
    if not os.path.exists(file_path):
        logging.warning(f"File {file_path} does not exist.")
        return {}

    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            logging.info(f"Loaded access points data from {file_path}.")
            return {ap['ssid']: ap for ap in data.get('access_points', [])}
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON from {file_path}: {e}")
        return {}

def compare_access_points(old_data, new_data):
    """Compare old and new access points data to find changes."""
    changes = []

    # Detect changes and removals
    for ssid, old_ap in old_data.items():
        if ssid not in new_data:
            changes.append(f"{ssid} is removed from the list")
        else:
            new_ap = new_data[ssid]
            if old_ap['snr'] != new_ap['snr']:
                changes.append(f"{ssid}’s SNR has changed from {old_ap['snr']} to {new_ap['snr']}")
            if old_ap['channel'] != new_ap['channel']:
                changes.append(f"{ssid}’s channel has changed from {old_ap['channel']} to {new_ap['channel']}")

    # Detect additions
    for ssid, new_ap in new_data.items():
        if ssid not in old_data:
            changes.append(f"{ssid} is added to the list with SNR {new_ap['snr']} and channel {new_ap['channel']}")

    return changes

def notify_app_b(changes):
    """Notify App B of the changes by sending data through RabbitMQ."""
    for attempt in range(5):  # Retry up to 5 times
        try:
            # Connect using the correct credentials
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_SERVER,
                    port=5672,
                    credentials=pika.PlainCredentials('user', 'password')  # Update with the correct credentials
                )
            )
            channel = connection.channel()

            # Declare an exchange of type 'fanout'
            channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type=EXCHANGE_TYPE)

            for change in changes:
                # Publish each change to the exchange
                channel.basic_publish(exchange=EXCHANGE_NAME, routing_key='', body=change)
                logging.info(f"Sent to exchange: {change}")

            # Close the connection
            connection.close()
            break  # Exit the retry loop if successful
        except Exception as e:
            logging.error(f"Failed to connect to RabbitMQ: {e}")
            time.sleep(5)  # Wait 5 seconds before retrying
    else:
        logging.error("Failed to connect to RabbitMQ after multiple attempts.")

def monitor_file():
    """Monitor the access points JSON file for changes."""
    logging.info(f"Starting to monitor {FILE_PATH} for changes.")
    previous_data = load_access_points(FILE_PATH)

    while True:
        time.sleep(5)  # Check for changes every 5 seconds
        current_data = load_access_points(FILE_PATH)

        if current_data != previous_data:
            changes = compare_access_points(previous_data, current_data)
            if changes:
                logging.info(f"Detected changes: {changes}")
                notify_app_b(changes)
            previous_data = current_data

if __name__ == "__main__":
    monitor_file()
