# Test ORM Connection
## Create file: test_orm.py (in project root)

# test_orm.py

import os
import sys
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import models
from src.models import (
    Base, User, Customer, Product, CustomerAffinity,
    CustomerProduct, OrchestrationDecision, RecommendationLog,
    CustomerEvent, BudgetTracker, InventoryAudit
)

# Database URL
DATABASE_URL = "sqlite:///./data/orchestrator.db"

def test_orm():
    """Test ORM connection and operations"""
    
    print("\n" + "="*60)
    print("TESTING ORM CONNECTION")
    print("="*60 + "\n")
    
    # Step 1: Create engine
    print("✓ Step 1: Creating database engine...")
    try:
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False}
        )
        print(f"  ✅ Engine created: {DATABASE_URL}\n")
    except Exception as e:
        print(f"  ❌ ERROR: {e}\n")
        return False
    
    # Step 2: Create tables
    print("✓ Step 2: Creating tables from ORM models...")
    try:
        Base.metadata.create_all(bind=engine)
        print("  ✅ Tables created successfully\n")
    except Exception as e:
        print(f"  ❌ ERROR: {e}\n")
        return False
    
    # Step 3: Verify tables exist
    print("✓ Step 3: Verifying tables exist...")
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        expected_tables = [
            'users', 'customers', 'customer_affinities', 'products',
            'customer_products', 'orchestration_decisions', 
            'recommendation_logs', 'customer_events', 
            'budget_tracker', 'inventory_audit'
        ]
        
        print(f"  Found {len(tables)} tables:")
        for table in sorted(tables):
            status = "✅" if table in expected_tables else "❓"
            print(f"    {status} {table}")
        
        if set(expected_tables).issubset(set(tables)):
            print("  ✅ All expected tables exist\n")
        else:
            missing = set(expected_tables) - set(tables)
            print(f"  ❌ Missing tables: {missing}\n")
            return False
    except Exception as e:
        print(f"  ❌ ERROR: {e}\n")
        return False
    
    # Step 4: Create session and test CRUD
    print("✓ Step 4: Testing CRUD operations...")
    try:
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        # CREATE: Insert a test user
        print("  - Testing CREATE (INSERT)...")
        test_user = User(
            user_id="TEST_USER_001",
            email="test@example.com",
            password_hash="$2b$12$test_hash_1234567890",
            is_active=True
        )
        session.add(test_user)
        session.commit()
        print("    ✅ User inserted successfully")
        
        # CREATE: Insert a test customer
        print("  - Testing CREATE (INSERT) for customer...")
        test_customer = Customer(
            customer_id="TEST_CUST_001",
            user_id="TEST_USER_001",
            segment="high_value",
            web_engagement=0.92,
            mobile_engagement=0.88,
            email_engagement=0.78,
            recency_days=2,
            frequency=15,
            monetary=1200.50
        )
        session.add(test_customer)
        session.commit()
        print("    ✅ Customer inserted successfully")
        
        # CREATE: Insert test product
        print("  - Testing CREATE (INSERT) for product...")
        test_product = Product(
            product_id="TEST_PROD_001",
            name="Test Lipstick",
            category="lipstick",
            price=40.00,
            inventory=50,
            rating=4.8,
            is_active=True
        )
        session.add(test_product)
        session.commit()
        print("    ✅ Product inserted successfully")
        
        # READ: Get user by ID
        print("  - Testing READ (SELECT) for user...")
        retrieved_user = session.query(User).filter(
            User.user_id == "TEST_USER_001"
        ).first()
        if retrieved_user:
            print(f"    ✅ Retrieved user: {retrieved_user.email}")
        else:
            print("    ❌ User not found")
            return False
        
        # READ: Get customer by ID
        print("  - Testing READ (SELECT) for customer...")
        retrieved_customer = session.query(Customer).filter(
            Customer.customer_id == "TEST_CUST_001"
        ).first()
        if retrieved_customer:
            print(f"    ✅ Retrieved customer: {retrieved_customer.customer_id}")
            print(f"       Segment: {retrieved_customer.segment}")
            print(f"       Monetary: ${retrieved_customer.monetary}")
        else:
            print("    ❌ Customer not found")
            return False
        
        # READ: Get product
        print("  - Testing READ (SELECT) for product...")
        retrieved_product = session.query(Product).filter(
            Product.product_id == "TEST_PROD_001"
        ).first()
        if retrieved_product:
            print(f"    ✅ Retrieved product: {retrieved_product.name}")
            print(f"       Price: ${retrieved_product.price}")
            print(f"       Inventory: {retrieved_product.inventory}")
        else:
            print("    ❌ Product not found")
            return False
        
        
        print("  - Testing UPDATE...")
        retrieved_customer.segment = "vip"
        session.commit()
        updated_customer = session.query(Customer).filter(
            Customer.customer_id == "TEST_CUST_001"
        ).first()
        if updated_customer.segment == "vip":
            print(f"    ✅ Customer updated: segment now {updated_customer.segment}")
        else:
            print("    ❌ Update failed")
            return False
        
        # Test Relationships
        print("  - Testing RELATIONSHIPS...")
        # Customer should have relationship to User
        if retrieved_customer.user:
            print(f"    ✅ Customer relationship to User: {retrieved_customer.user.email}")
        else:
            print("    ❌ Relationship not working")
            return False
        
        # DELETE: Delete test data
        print("  - Testing DELETE...")
        session.delete(retrieved_customer)
        session.delete(retrieved_product)
        session.delete(retrieved_user)
        session.commit()
        print("    ✅ Test data deleted successfully")
        
        session.close()
        print("  ✅ All CRUD operations successful\n")
        
    except Exception as e:
        print(f"  ❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 5: Test with sample data
    print("✓ Step 5: Testing with sample data from database...")
    try:
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        # Query existing customers (from schema.sql)
        customers = session.query(Customer).all()
        if customers:
            print(f"  ✅ Found {len(customers)} customer(s) in database:")
            for customer in customers:
                print(f"    - {customer.customer_id}: {customer.segment} (${customer.monetary})")
        else:
            print("  ⚠️  No customers found (database might be empty)")
        
        # Query existing products
        products = session.query(Product).all()
        if products:
            print(f"  ✅ Found {len(products)} product(s) in database:")
            for product in products:
                print(f"    - {product.product_id}: {product.name} (${product.price})")
        else:
            print("  ⚠️  No products found")
        
        session.close()
        
    except Exception as e:
        print(f"  ⚠️  Warning: {e}\n")
    
    print("="*60)
    print("✅ ORM TEST PASSED!")
    print("="*60 + "\n")
    
    return True

if __name__ == "__main__":
    success = test_orm()
    sys.exit(0 if success else 1)
