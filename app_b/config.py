import os

class Config:
    RABBITMQ_USER = os.getenv('RABBITMQ_USER')
    RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD')
    RABBITMQ_SERVER= os.getenv('RABBITMQ_SERVER')

    @classmethod
    def print_config(cls):
        """Prints the RabbitMQ configuration details."""
        print(f"RABBITMQ_USER: {cls.RABBITMQ_USER}")
        print(f"RABBITMQ_PASSWORD: {cls.RABBITMQ_PASSWORD}")


if __name__ == "__main__":
    Config.print_config()