from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="StoreBuddy API",
    description="AI-powered retail management system",
    version="1.0.0"
)

# Data Models
class Product(BaseModel):
    id: int
    name: str
    barcode: Optional[str] = None
    price: float
    quantity: int
    category: Optional[str] = "General"

class Customer(BaseModel):
    id: int
    name: str
    phone: Optional[str] = None
    loyalty_points: int = 0

class BillItem(BaseModel):
    product_id: int
    quantity: int

class Bill(BaseModel):
    bill_id: int
    items: List[BillItem]
    customer_id: Optional[int] = None
    subtotal: float
    gst_amount: float
    total: float
    timestamp: datetime

# In-memory storage
products_db = []
customers_db = []
bills_db = []
bill_counter = 0

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "Welcome to StoreBuddy API!",
        "version": "1.0.0",
        "status": "running"
    }

# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

# PRODUCT ENDPOINTS
@app.get("/products", response_model=List[Product])
def get_all_products():
    return products_db

@app.post("/products", response_model=Product)
def add_product(product: Product):
    # Check if product ID already exists
    for existing_product in products_db:
        if existing_product.id == product.id:
            raise HTTPException(status_code=400, detail="Product ID already exists")
    
    products_db.append(product)
    return product

@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int):
    for product in products_db:
        if product.id == product_id:
            return product
    raise HTTPException(status_code=404, detail="Product not found")

@app.put("/products/{product_id}", response_model=Product)
def update_product(product_id: int, updated_product: Product):
    for i, product in enumerate(products_db):
        if product.id == product_id:
            updated_product.id = product_id
            products_db[i] = updated_product
            return updated_product
    raise HTTPException(status_code=404, detail="Product not found")

@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    for i, product in enumerate(products_db):
        if product.id == product_id:
            del products_db[i]
            return {"message": "Product deleted successfully"}
    raise HTTPException(status_code=404, detail="Product not found")

# CUSTOMER ENDPOINTS
@app.get("/customers", response_model=List[Customer])
def get_all_customers():
    return customers_db

@app.post("/customers", response_model=Customer)
def add_customer(customer: Customer):
    # Check if customer ID already exists
    for existing_customer in customers_db:
        if existing_customer.id == customer.id:
            raise HTTPException(status_code=400, detail="Customer ID already exists")
    
    customers_db.append(customer)
    return customer

# BILLING ENDPOINTS
@app.post("/bill", response_model=dict)
def create_bill(items: List[BillItem], customer_id: Optional[int] = None):
    global bill_counter
    bill_counter += 1
    
    subtotal = 0.0
    bill_items_processed = []
    
    # Process each item
    for item in items:
        # Find the product
        product = None
        for p in products_db:
            if p.id == item.product_id:
                product = p
                break
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} not found")
        
        if product.quantity < item.quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient stock for {product.name}. Available: {product.quantity}, Requested: {item.quantity}"
            )
        
        # Calculate item total
        item_total = product.price * item.quantity
        subtotal += item_total
        
        # Update inventory
        product.quantity -= item.quantity
        
        # Track processed item
        bill_items_processed.append({
            "product_id": product.id,
            "product_name": product.name,
            "quantity": item.quantity,
            "unit_price": product.price,
            "item_total": item_total
        })
    
    # Calculate GST (18%)
    gst_amount = round(subtotal * 0.18, 2)
    total = round(subtotal + gst_amount, 2)
    
    # Create bill record
    bill_record = {
        "bill_id": bill_counter,
        "customer_id": customer_id,
        "items": bill_items_processed,
        "subtotal": subtotal,
        "gst_amount": gst_amount,
        "total": total,
        "timestamp": datetime.now().isoformat()
    }
    
    bills_db.append(bill_record)
    
    return {
        "success": True,
        "bill": bill_record,
        "message": f"Bill #{bill_counter} created successfully"
    }

# REPORTS ENDPOINTS
@app.get("/reports/daily-sales")
def get_daily_sales():
    today = datetime.now().date()
    daily_bills = [
        bill for bill in bills_db 
        if datetime.fromisoformat(bill["timestamp"]).date() == today
    ]
    
    total_sales = sum(bill["total"] for bill in daily_bills)
    total_bills = len(daily_bills)
    
    return {
        "date": today.isoformat(),
        "total_bills": total_bills,
        "total_sales": total_sales,
        "bills": daily_bills
    }

@app.get("/reports/inventory-status")
def get_inventory_status():
    low_stock_products = [p for p in products_db if p.quantity < 10]
    out_of_stock = [p for p in products_db if p.quantity == 0]
    
    return {
        "total_products": len(products_db),
        "low_stock_items": len(low_stock_products),
        "out_of_stock_items": len(out_of_stock),
        "low_stock_products": low_stock_products,
        "out_of_stock_products": out_of_stock
    }

# AI FEATURES (Placeholders)
@app.get("/ai/marketing")
def ai_marketing():
    return {
        "message": "AI Marketing feature",
        "suggestions": [
            "Promote Festival Sale for top 5 products",
            "Send loyalty offers to customers with 100+ points",
            "Create social media post for new arrivals"
        ]
    }

@app.get("/ai/demand-forecast")
def demand_forecast():
    return {
        "message": "AI Demand Forecasting",
        "predictions": [
            {"product_id": 1, "predicted_demand": 25, "confidence": 85},
            {"product_id": 2, "predicted_demand": 18, "confidence": 78}
        ]
    }

# Run the application
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
