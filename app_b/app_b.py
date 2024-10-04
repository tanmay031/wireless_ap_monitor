import pika
import os
import logging
import time

# RabbitMQ server details from environment variables
RABBITMQ_SERVER = os.getenv('RABBITMQ_SERVER', 'rabbitmq')
RABBITMQ_USERNAME = os.getenv('RABBITMQ_USER', 'user')  
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'password')  # Default to 'guest' if not set
EXCHANGE_NAME = 'ap_changes'

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RabbitMQListener:
    def __init__(self, server, exchange_name, username, password, retries=12):
        """Initialize the listener with RabbitMQ connection details."""
        self.server = server
        self.exchange_name = exchange_name
        self.username = username
        self.password = password
        self.retries = retries
        self.connection = None
        self.channel = None

    def callback(self, ch, method, properties, body):
        """Callback function to process received messages."""
        message = body.decode('utf-8')
        logging.info(f"Received: {message}")

    def connect(self):
        """Connect to RabbitMQ with retry logic."""
        for attempt in range(self.retries):
            try:
                # Establish connection to RabbitMQ
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=self.server,
                        port=5672,
                        credentials=pika.PlainCredentials(self.username, self.password)
                    )
                )
                self.channel = self.connection.channel()

                # Declare the exchange
                self.channel.exchange_declare(exchange=self.exchange_name, exchange_type='fanout')

                return True  # Successful connection
            except Exception as e:
                logging.error(f"Failed to connect to RabbitMQ (attempt {attempt + 1}/{self.retries}): {e}")
                time.sleep(5)  # Wait for 5 seconds before retrying
        return False  # Failed to connect after all retries

    def start_listening(self):
        """Start listening to the RabbitMQ exchange for messages."""
        if not self.connect():
            logging.error("Failed to connect to RabbitMQ after multiple attempts.")
            return

        # Create a temporary queue with a random name
        result = self.channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue

        # Bind the queue to the exchange
        self.channel.queue_bind(exchange=self.exchange_name, queue=queue_name)

        logging.info(f"Listening for messages on exchange '{self.exchange_name}'...")

        # Subscribe to the queue
        self.channel.basic_consume(queue=queue_name, on_message_callback=self.callback, auto_ack=True)

        try:
            # Start consuming messages
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logging.info("Listener stopped.")
        finally:
            if self.connection:
                self.connection.close()

if __name__ == "__main__":
    # Initialize the listener with credentials from environment variables
    listener = RabbitMQListener(
        server=RABBITMQ_SERVER, 
        exchange_name=EXCHANGE_NAME, 
        username=RABBITMQ_USERNAME, 
        password=RABBITMQ_PASSWORD
    )
    listener.start_listening()
