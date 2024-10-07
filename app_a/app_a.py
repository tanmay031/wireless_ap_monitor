import json
import time
import os
import pika
import logging
from config import Config


class FileMonitor:
    def __init__(self, file_path, exchange_name, exchange_type):
        self.file_path = file_path
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type
        self.previous_data = {}

    def load_access_points(self):
        """Load access points data from a JSON file."""
        if not os.path.exists(self.file_path):
            logging.warning(f"File {self.file_path} does not exist.")
            return {}

        try:
            with open(self.file_path, 'r') as file:
                data = json.load(file)
                logging.info(f"Loaded access points data from {self.file_path}.")
                return {ap['ssid']: ap for ap in data.get('access_points', [])}
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON from {self.file_path}: {e}")
            return {}

    def compare_access_points(self, new_data):
        """Compare old and new access points data to find changes."""
        changes = []

        # Detect changes and removals
        for ssid, old_ap in self.previous_data.items():
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
            if ssid not in self.previous_data:
                changes.append(f"{ssid} is added to the list with SNR {new_ap['snr']} and channel {new_ap['channel']}")

        return changes

    def connect_to_rabbitmq(self):
        """Establish a connection to RabbitMQ and return the connection object."""
        
        for attempt in range(5):  # Retry up to 5 times
            try:
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=Config.RABBITMQ_SERVER,
                        port=5672,
                        credentials=pika.PlainCredentials(Config.RABBITMQ_USER, Config.RABBITMQ_PASSWORD)
                    )
                )
                return connection
            except Exception as e:
                logging.error(f"Failed to connect to RabbitMQ: {e}")
                time.sleep(5)  # Wait 5 seconds before retrying
        logging.error("Failed to connect to RabbitMQ after multiple attempts.")
        return None

    def publish_changes(self, connection, changes):
        """Publish the changes to the RabbitMQ exchange using an established connection."""
        
        try:
            channel = connection.channel()

            # Declare an exchange of type 'fanout'
            channel.exchange_declare(exchange=self.exchange_name, exchange_type=self.exchange_type)

            for change in changes:
                # Publish each change to the exchange
                channel.basic_publish(exchange=self.exchange_name, routing_key='', body=change)
                logging.info(f"Sent to exchange: {change}")
        except Exception as e:
            logging.error(f"Error while publishing changes: {e}")
        finally:
            # Close the connection
            connection.close()
    def notify_app_b(self, changes):
        """Notify App B of the changes by sending data through RabbitMQ."""
        
        # Step 1: Establish a connection to RabbitMQ
        connection = self.connect_to_rabbitmq()
        
        # Step 2: Publish changes if connection was successful
        if connection:
            self.publish_changes(connection, changes)
        else:
            logging.error("Cannot notify App B. No RabbitMQ connection established.")

    def monitor_file(self):
        """Monitor the access points JSON file for changes."""
        logging.info(f"Starting to monitor {self.file_path} for changes.")
        self.previous_data = self.load_access_points()

        while True:
            time.sleep(5)  # Check for changes every 5 seconds
            current_data = self.load_access_points()

            if current_data != self.previous_data:
                changes = self.compare_access_points(current_data)
                if changes:
                    logging.info(f"Detected changes: {changes}")
                    self.notify_app_b(changes)
                self.previous_data = current_data


if __name__ == "__main__":
    # File path to monitor (located in the current directory inside the container)
    FILE_PATH = './access_points.json'

    # Exchange info
    EXCHANGE_NAME = 'ap_changes'
    EXCHANGE_TYPE = 'fanout'  # 'fanout' exchange broadcasts messages to all queues

    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Instantiate and run the FileMonitor
    monitor = FileMonitor(FILE_PATH, EXCHANGE_NAME, EXCHANGE_TYPE)
    monitor.monitor_file()
