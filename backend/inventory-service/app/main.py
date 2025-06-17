from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import json
from confluent_kafka import Producer, Consumer
import os
from pymongo import MongoClient
import threading
import time

app = FastAPI(title="Inventory Service")

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = MongoClient(MONGODB_URI)
db = client.inventory_db
inventory = db.inventory
inventory_updates = db.inventory_updates

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# Kafka producer
producer = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})

def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed for record {msg.key()}: {err}")
    else:
        print(f"Record {msg.key()} successfully produced to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

class InventoryItem(BaseModel):
    product_id: str
    quantity: int
    price: float

def initialize_inventory():
    """Initialize inventory with some sample products"""
    sample_products = [
        {"product_id": "P001", "quantity": 100, "price": 29.99},
        {"product_id": "P002", "quantity": 50, "price": 49.99},
        {"product_id": "P003", "quantity": 75, "price": 19.99}
    ]
    
    for product in sample_products:
        inventory.update_one(
            {"product_id": product["product_id"]},
            {"$set": product},
            upsert=True
        )

def update_inventory(order_data):
    """Update inventory based on order items"""
    time.sleep(1)  # Simulate inventory update time
    
    # Get order items from order service
    items = order_data.get("items", [])
    
    # Update inventory for each item
    for item in items:
        inventory.update_one(
            {"product_id": item["product_id"]},
            {"$inc": {"quantity": -item["quantity"]}}
        )
    
    # Record inventory update
    update_doc = {
        "order_id": order_data["order_id"],
        "items": items,
        "timestamp": datetime.utcnow()
    }
    inventory_updates.insert_one(update_doc)
    
    # Send inventory_updated event
    payload = {
        "order_id": order_data["order_id"],
        "status": "UPDATED",
        "timestamp": datetime.utcnow().isoformat()
    }
    producer.produce(
        "inventory_updated",
        key=order_data["order_id"],
        value=json.dumps(payload).encode('utf-8'),
        callback=delivery_report
    )
    producer.flush()

def consume_payments():
    """Consume payment_processed events and update inventory"""
    consumer = Consumer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': 'inventory-service',
        'auto.offset.reset': 'earliest'
    })
    consumer.subscribe(['payment_processed'])
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue
        payment_data = json.loads(msg.value().decode('utf-8'))
        # Fetch order details from order service
        # For now, we'll use a mock order data
        order_data = {
            "order_id": payment_data["order_id"],
            "items": [
                {"product_id": "P001", "quantity": 2, "price": 29.99},
                {"product_id": "P002", "quantity": 1, "price": 49.99}
            ]
        }
        update_inventory(order_data)

# Initialize inventory
initialize_inventory()

# Start Kafka consumer in a background thread
consumer_thread = threading.Thread(target=consume_payments, daemon=True)
consumer_thread.start()

@app.get("/inventory/{product_id}")
def get_inventory(product_id: str):
    item = inventory.find_one({"product_id": product_id})
    if not item:
        return {"status": "not_found"}
    return {
        "product_id": item["product_id"],
        "quantity": item["quantity"],
        "price": item["price"]
    }

@app.get("/inventory")
def list_inventory():
    items = list(inventory.find())
    return items

@app.get("/health")
def health_check():
    return {"status": "healthy"} 