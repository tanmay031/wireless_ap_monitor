import pika
import os
import logging
import time
from config import Config


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RabbitMQListener:
    def __init__(self, exchange_name, exchange_type, retries=10):
        """Initialize the listener with RabbitMQ connection details."""
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type
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
                        host=Config.RABBITMQ_SERVER,
                        port=5672,
                        credentials=pika.PlainCredentials(Config.RABBITMQ_USER, Config.RABBITMQ_PASSWORD)
                    )
                )
                self.channel = self.connection.channel()

                # Declare the exchange
                self.channel.exchange_declare(exchange=self.exchange_name, exchange_type=self.exchange_type)

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
    
    # Exchange info
    EXCHANGE_NAME = 'ap_changes'
    EXCHANGE_TYPE = 'fanout'  # 'fanout' exchange broadcasts messages to all queues
    
    # Initialize the listener with credentials from environment variables
    listener = RabbitMQListener(
        exchange_name=EXCHANGE_NAME, 
        exchange_type=EXCHANGE_TYPE
    )
    listener.start_listening()
