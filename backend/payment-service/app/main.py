from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
import json
from confluent_kafka import Producer, Consumer
import os
from pymongo import MongoClient
import threading
import time

app = FastAPI(title="Payment Service")

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = MongoClient(MONGODB_URI)
db = client.payment_db
payments = db.payments

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# Kafka producer
producer = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})

def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed for record {msg.key()}: {err}")
    else:
        print(f"Record {msg.key()} successfully produced to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

class Payment(BaseModel):
    order_id: str
    amount: float
    status: str
    timestamp: datetime

def process_payment(order_data):
    """Simulate payment processing"""
    time.sleep(2)  # Simulate payment processing time
    
    # Create payment record
    payment_doc = {
        "order_id": order_data["order_id"],
        "amount": order_data["total_amount"],
        "status": "COMPLETED",
        "timestamp": datetime.utcnow()
    }
    
    # Save to MongoDB
    payments.insert_one(payment_doc)
    
    # Send payment_processed event
    payload = {
        "order_id": order_data["order_id"],
        "status": "COMPLETED",
        "timestamp": datetime.utcnow().isoformat()
    }
    producer.produce(
        "payment_processed",
        key=order_data["order_id"],
        value=json.dumps(payload).encode('utf-8'),
        callback=delivery_report
    )
    producer.flush()

def consume_orders():
    """Consume order_placed events and process payments"""
    consumer = Consumer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': 'payment-service',
        'auto.offset.reset': 'earliest'
    })
    consumer.subscribe(['order_placed'])
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue
        order_data = json.loads(msg.value().decode('utf-8'))
        process_payment(order_data)

# Start Kafka consumer in a background thread
consumer_thread = threading.Thread(target=consume_orders, daemon=True)
consumer_thread.start()

@app.get("/payments/{order_id}")
def get_payment(order_id: str):
    payment = payments.find_one({"order_id": order_id})
    if not payment:
        return {"status": "not_found"}
    return {
        "order_id": payment["order_id"],
        "amount": payment["amount"],
        "status": payment["status"],
        "timestamp": payment["timestamp"]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"} 