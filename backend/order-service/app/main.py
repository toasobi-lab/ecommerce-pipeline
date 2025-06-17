from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
from confluent_kafka import Producer
import os
from pymongo import MongoClient
from bson import ObjectId

app = FastAPI(title="Order Service")

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = MongoClient(MONGODB_URI)
db = client.order_db
orders = db.orders

# Kafka producer
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
producer = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})

def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed for record {msg.key()}: {err}")
    else:
        print(f"Record {msg.key()} successfully produced to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

class OrderItem(BaseModel):
    product_id: str
    quantity: int
    price: float

class Order(BaseModel):
    customer_id: str
    items: List[OrderItem]
    shipping_address: str
    total_amount: float

class OrderResponse(BaseModel):
    order_id: str
    status: str
    created_at: datetime
    customer_id: str
    items: List[OrderItem]
    shipping_address: str
    total_amount: float

@app.post("/orders", response_model=OrderResponse)
def create_order(order: Order):
    # Create order document
    order_doc = {
        "customer_id": order.customer_id,
        "items": [item.dict() for item in order.items],
        "shipping_address": order.shipping_address,
        "total_amount": order.total_amount,
        "status": "PENDING",
        "created_at": datetime.utcnow()
    }
    
    # Save to MongoDB
    result = orders.insert_one(order_doc)
    order_doc["_id"] = result.inserted_id
    
    # Send to Kafka
    payload = {
        "order_id": str(result.inserted_id),
        "customer_id": order.customer_id,
        "items": [item.dict() for item in order.items],
        "total_amount": order.total_amount,
        "timestamp": datetime.utcnow().isoformat()
    }
    producer.produce(
        "order_placed",
        key=str(result.inserted_id),
        value=json.dumps(payload).encode('utf-8'),
        callback=delivery_report
    )
    producer.flush()
    
    return {
        "order_id": str(result.inserted_id),
        "status": "PENDING",
        "created_at": order_doc["created_at"],
        "customer_id": order.customer_id,
        "items": order.items,
        "shipping_address": order.shipping_address,
        "total_amount": order.total_amount
    }

@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str):
    order = orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {
        "order_id": str(order["_id"]),
        "status": order["status"],
        "created_at": order["created_at"],
        "customer_id": order["customer_id"],
        "items": order["items"],
        "shipping_address": order["shipping_address"],
        "total_amount": order["total_amount"]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"} 