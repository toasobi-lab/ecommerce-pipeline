# E-commerce Pipeline with Kafka Microservices

## 🚀 Educational Goals

This project is designed to help you **learn and apply Kafka concepts** in a real-world microservices architecture. By building and running this e-commerce pipeline, you will:

- Understand **Kafka core concepts**: producers, consumers, topics, partitions, offsets
- See **event-driven architecture** in action
- Orchestrate microservices with **Docker Compose**
- Build microservices with **FastAPI (Python)**
- Use **MongoDB** as a backing store
- Monitor and debug with **Kafdrop** and **Mongo Express**

---

## 🏗️ Architecture Overview

The system consists of four main microservices, each responsible for a stage in the e-commerce order pipeline:

- **Order Service**: Accepts orders and publishes `order_placed` events
- **Payment Service**: Processes payments and publishes `payment_processed` events
- **Inventory Service**: Updates inventory and publishes `inventory_updated` events
- **Shipment Service**: Handles shipping and order fulfillment

**Supporting infrastructure:**
- **Kafka** (with Zookeeper): Message broker for event streaming
- **MongoDB**: Data persistence for each service
- **Kafdrop**: Kafka topic/message monitoring UI
- **Mongo Express**: MongoDB web UI

---

## 🖼️ System Architecture Diagram (ASCII)

```
+------------------+     +------------------+     +------------------+     +------------------+
|   Order Service  |     | Payment Service  |     |Inventory Service |     | Shipment Service |
|  (Port: 8001)    |     |  (Port: 8002)    |     |  (Port: 8003)    |     |  (Port: 8004)    |
+------------------+     +------------------+     +------------------+     +------------------+
         |                       |                       |                       |
         v                       v                       v                       v
+------------------+     +------------------+     +------------------+     +------------------+
|   MongoDB        |     |   MongoDB        |     |   MongoDB        |     |   MongoDB        |
+------------------+     +------------------+     +------------------+     +------------------+
         ^                       ^                       ^                       ^
         |                       |                       |                       |
+------------------+     +------------------+     +------------------+     +------------------+
|   Kafka Topics   |     |   Kafka Topics   |     |   Kafka Topics   |     |   Kafka Topics   |
|  - order_placed  |     |  - payment_      |     |  - inventory_    |     |  - shipment_     |
|                  |     |    processed     |     |    updated       |     |    processed     |
+------------------+     +------------------+     +------------------+     +------------------+
         ^                       ^                       ^                       ^
         |                       |                       |                       |
+------------------+     +------------------+     +------------------+     +------------------+
|   Zookeeper      |     |   Kafdrop        |     | Mongo Express    |     |                  |
+------------------+     +------------------+     +------------------+     +------------------+
```

---

## 🔄 Data Flow: Kafka Event-Driven Pipeline

1. **Order Creation**
   - Client → Order Service → MongoDB
   - Order Service publishes `order_placed` event to Kafka
2. **Payment Processing**
   - Payment Service consumes `order_placed`, processes payment, stores in MongoDB
   - Publishes `payment_processed` event
3. **Inventory Update**
   - Inventory Service consumes `payment_processed`, updates stock, stores in MongoDB
   - Publishes `inventory_updated` event
4. **Shipment Processing**
   - Shipment Service consumes `inventory_updated`, creates shipment, stores in MongoDB

---

## 🛠️ Getting Started

### Prerequisites
- [Docker](https://www.docker.com/products/docker-desktop/) and Docker Compose installed
- Basic knowledge of Python and REST APIs

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd ecommerce-pipeline
```

### 2. Start all services
```bash
docker-compose up --build
```

### 3. Access the tools
- **Order Service**: http://localhost:8001
- **Payment Service**: http://localhost:8002
- **Inventory Service**: http://localhost:8003
- **Shipment Service**: http://localhost:8004
- **Kafdrop (Kafka UI)**: http://localhost:9000
- **Mongo Express**: http://localhost:8081

---

## 🧪 Testing the Pipeline (Step-by-Step)

### 1. Send a Test Order
```bash
curl -X POST http://localhost:8001/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST001",
    "items": [
      {"product_id": "P001", "quantity": 2, "price": 29.99},
      {"product_id": "P002", "quantity": 1, "price": 49.99}
    ],
    "shipping_address": "123 Main St, City, Country",
    "total_amount": 109.97
  }'
```
- You should get a JSON response with an `order_id`.

### 2. Watch the Event Flow
- **Kafdrop UI:** Open [http://localhost:9000](http://localhost:9000) and watch messages in topics like `order_placed`, `payment_processed`, `inventory_updated`.
- **Mongo Express:** Open [http://localhost:8081](http://localhost:8081) and browse the MongoDB collections for each service.

### 3. Check Each Service's Status
Replace `{order_id}` with the ID from the order creation step.

- **Order status:**
  ```bash
  curl http://localhost:8001/orders/{order_id}
  ```
- **Payment status:**
  ```bash
  curl http://localhost:8002/payments/{order_id}
  ```
- **Inventory (list all):**
  ```bash
  curl http://localhost:8003/inventory
  ```
- **Shipment status:**
  ```bash
  curl http://localhost:8004/shipments/{order_id}
  ```

---

## 📚 What You'll Learn

- **Kafka basics**: How producers and consumers work, and how topics connect services
- **Event-driven microservices**: How to decouple services using events
- **Service orchestration**: How Docker Compose manages multi-container apps
- **Real-world debugging**: Using Kafdrop and Mongo Express to inspect data and events
- **Resilience**: How services recover and retry when Kafka or MongoDB are temporarily unavailable

---

## 📝 Next Steps & Experiments
- Try breaking a service and see how the pipeline recovers
- Add a new microservice (e.g., email notification)
- Change the data model or add new Kafka topics
- Explore scaling by running multiple consumer instances

---

Happy learning! 🚀 