from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import json
from confluent_kafka import Consumer
import os
from pymongo import MongoClient
import threading
import time
import uuid

app = FastAPI(title="Shipment Service")

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = MongoClient(MONGODB_URI)
db = client.shipment_db
shipments = db.shipments

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

class Shipment(BaseModel):
    shipment_id: str
    order_id: str
    status: str
    tracking_number: str
    created_at: datetime
    estimated_delivery: datetime

def process_shipment(order_id: str):
    """Process shipment for an order"""
    time.sleep(2)  # Simulate shipment processing time
    
    # Generate tracking number
    tracking_number = f"TRK-{uuid.uuid4().hex[:8].upper()}"
    
    # Create shipment record
    shipment_doc = {
        "shipment_id": str(uuid.uuid4()),
        "order_id": order_id,
        "status": "PROCESSING",
        "tracking_number": tracking_number,
        "created_at": datetime.utcnow(),
        "estimated_delivery": datetime.utcnow().replace(day=datetime.utcnow().day + 3)
    }
    
    # Save to MongoDB
    shipments.insert_one(shipment_doc)
    
    # Update shipment status after a delay
    time.sleep(3)
    shipments.update_one(
        {"order_id": order_id},
        {"$set": {"status": "SHIPPED"}}
    )

def consume_inventory_updates():
    """Consume inventory_updated events and process shipments"""
    consumer = Consumer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': 'shipment-service',
        'auto.offset.reset': 'earliest'
    })
    consumer.subscribe(['inventory_updated'])
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue
        inventory_data = json.loads(msg.value().decode('utf-8'))
        process_shipment(inventory_data["order_id"])

# Start Kafka consumer in a background thread
consumer_thread = threading.Thread(target=consume_inventory_updates, daemon=True)
consumer_thread.start()

@app.get("/shipments/{order_id}")
def get_shipment(order_id: str):
    shipment = shipments.find_one({"order_id": order_id})
    if not shipment:
        return {"status": "not_found"}
    return {
        "shipment_id": shipment["shipment_id"],
        "order_id": shipment["order_id"],
        "status": shipment["status"],
        "tracking_number": shipment["tracking_number"],
        "created_at": shipment["created_at"],
        "estimated_delivery": shipment["estimated_delivery"]
    }

@app.get("/shipments")
def list_shipments():
    items = list(shipments.find())
    return items

@app.get("/health")
def health_check():
    return {"status": "healthy"} 