# app_b/app_b.py
import pika
import os
import logging
import time

# RabbitMQ server details
RABBITMQ_SERVER = os.getenv('RABBITMQ_SERVER', 'rabbitmq')
EXCHANGE_NAME = 'ap_changes'

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def callback(ch, method, properties, body):
    """Callback function to process received messages."""
    message = body.decode('utf-8')
    logging.info(f"Received: {message}")

def start_listener():
    """Connect to RabbitMQ and start listening for messages."""
    for attempt in range(12):  # Retry up to 5 times
        try:
            # Connect to RabbitMQ using the specified credentials
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_SERVER,
                    port=5672,
                    credentials=pika.PlainCredentials('user', 'password')  # Use the correct credentials
                )
            )
            channel = connection.channel()

            # Declare the exchange
            channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout')

            # Create a temporary queue with a random name
            result = channel.queue_declare(queue='', exclusive=True)
            queue_name = result.method.queue

            # Bind the queue to the exchange
            channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name)

            logging.info(f"Listening for messages on exchange '{EXCHANGE_NAME}'...")

            # Subscribe to the queue
            channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

            # Start consuming messages
            channel.start_consuming()
            break  # Exit the retry loop if successful
        except Exception as e:
            logging.error(f"Failed to connect to RabbitMQ: {e}")
            time.sleep(5)  # Wait for 5 seconds before retrying
    else:
        logging.error("Failed to connect to RabbitMQ after multiple attempts.")

if __name__ == "__main__":
    start_listener()
