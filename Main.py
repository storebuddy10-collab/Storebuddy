from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="StoreBuddy API")

# Allow CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class Product(BaseModel):
    id: int
    name: str
    barcode: str = None
    price: float
    quantity: int

class Customer(BaseModel):
    id: int
    name: str
    phone: str = None
    loyalty_points: int = 0

class BillItem(BaseModel):
    product_id: int
    quantity: int

# In-memory storage (replace with DB in real app)
products = []
customers = []
bill_count = 0

# Inventory routes
@app.get("/products", response_model=List[Product])
def list_products():
    return products

@app.post("/products", response_model=Product)
def add_product(product: Product):
    for p in products:
        if p.id == product.id:
            raise HTTPException(status_code=400, detail="Product ID already exists")
    products.append(product)
    return product

@app.put("/products/{product_id}", response_model=Product)
def update_product(product_id: int, product: Product):
    for i, p in enumerate(products):
        if p.id == product_id:
            products[i] = product
            return product
    raise HTTPException(status_code=404, detail="Product not found")

# Billing route with GST (18%)
@app.post("/bill")
def create_bill(items: List[BillItem]):
    total = 0.0
    for item in items:
        product = next((p for p in products if p.id == item.product_id), None)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} not found")
        if product.quantity < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient quantity for product {product.name}")
        total += product.price * item.quantity
    gst = round(total * 0.18, 2)
    grand_total = total + gst
    global bill_count
    bill_count += 1
    return {
        "bill_number": bill_count,
        "total": total,
        "gst": gst,
        "grand_total": grand_total,
        "items": items
    }

# Customer routes
@app.get("/customers", response_model=List[Customer])
def list_customers():
    return customers

@app.post("/customers", response_model=Customer)
def add_customer(customer: Customer):
    for c in customers:
        if c.id == customer.id:
            raise HTTPException(status_code=400, detail="Customer ID exists")
    customers.append(customer)
    return customer

# Placeholder routes for AI marketing etc.
@app.get("/ai-marketing")
def ai_marketing():
    return {"message": "AI Marketing feature coming soon"}

@app.get("/franchise-management")
def franchise_management():
    return {"message": "Franchise Management feature coming soon"}

@app.get("/accounting")
def accounting():
    return {"message": "Accounting feature coming soon"}
  
