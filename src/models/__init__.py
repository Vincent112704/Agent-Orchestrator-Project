# SQLAlchemy ORM Models
## src/models/__init__.py

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

# Create base class for all models
Base = declarative_base()

# ============================================================
# 1. USER MODEL
# ============================================================
class User(Base):
    """User authentication model"""
    __tablename__ = "users"
    
    user_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, email={self.email})>"


# ============================================================
# 2. CUSTOMER MODEL
# ============================================================
class Customer(Base):
    """Customer profile and engagement metrics"""
    __tablename__ = "customers"
    
    customer_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    # Segment classification
    segment = Column(String(50), default="new", nullable=False, index=True)
    
    # Engagement metrics (0.0 - 1.0)
    web_engagement = Column(Float, default=0.5)
    mobile_engagement = Column(Float, default=0.5)
    email_engagement = Column(Float, default=0.5)
    
    # Email preferences
    email_unsubscribed = Column(Boolean, default=False)
    email_frequency_max_per_week = Column(Integer, default=3)
    email_last_sent_at = Column(DateTime, nullable=True)
    
    # RFM metrics
    recency_days = Column(Integer, default=999, index=True)
    frequency = Column(Integer, default=0)
    frequency_period = Column(String(20), default="90_days")
    monetary = Column(Float, default=0.00, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("segment IN ('new', 'at_risk', 'loyal', 'high_value', 'vip')"),
    )
    
    # Relationships
    user = relationship("User", back_populates="customer")
    affinities = relationship("CustomerAffinity", back_populates="customer", cascade="all, delete-orphan")
    products = relationship("CustomerProduct", back_populates="customer", cascade="all, delete-orphan")
    orchestration_decisions = relationship("OrchestrationDecision", back_populates="customer", cascade="all, delete-orphan")
    events = relationship("CustomerEvent", back_populates="customer", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Customer(customer_id={self.customer_id}, segment={self.segment}, monetary={self.monetary})>"


# ============================================================
# 3. CUSTOMER AFFINITY MODEL
# ============================================================
class CustomerAffinity(Base):
    """Product category affinity scores for customers"""
    __tablename__ = "customer_affinities"
    
    affinity_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(36), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    affinity_score = Column(Float, nullable=False, index=True)
    updated_reason = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint: one affinity per customer per category
    __table_args__ = (
        UniqueConstraint("customer_id", "category", name="unique_customer_category"),
    )
    
    # Relationships
    customer = relationship("Customer", back_populates="affinities")
    
    def __repr__(self):
        return f"<CustomerAffinity(customer_id={self.customer_id}, category={self.category}, score={self.affinity_score})>"


# ============================================================
# 4. PRODUCT MODEL
# ============================================================
class Product(Base):
    """Product catalog"""
    __tablename__ = "products"
    
    product_id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    price = Column(Float, nullable=False)
    inventory = Column(Integer, default=0, nullable=False, index=True)
    rating = Column(Float, default=0.0)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer_products = relationship("CustomerProduct", back_populates="product", cascade="all, delete-orphan")
    recommendation_logs = relationship("RecommendationLog", back_populates="product")
    inventory_audits = relationship("InventoryAudit", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Product(product_id={self.product_id}, name={self.name}, price={self.price}, inventory={self.inventory})>"


# ============================================================
# 5. CUSTOMER PRODUCT MODEL
# ============================================================
class CustomerProduct(Base):
    """Customer-product interactions"""
    __tablename__ = "customer_products"
    
    customer_product_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(36), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False, index=True)
    interaction_type = Column(String(50), nullable=False, index=True)
    interaction_count = Column(Integer, default=1)
    last_interaction_at = Column(DateTime, nullable=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("interaction_type IN ('view', 'click', 'add_to_cart', 'purchase', 'wishlist', 'email_open', 'email_click', 'recommendation_shown')"),
        Index("idx_customer_product_composite", "customer_id", "product_id", "interaction_type"),
    )
    
    # Relationships
    customer = relationship("Customer", back_populates="products")
    product = relationship("Product", back_populates="customer_products")
    
    def __repr__(self):
        return f"<CustomerProduct(customer_id={self.customer_id}, product_id={self.product_id}, interaction={self.interaction_type})>"


# ============================================================
# 6. ORCHESTRATION DECISION MODEL
# ============================================================
class OrchestrationDecision(Base):
    """Log of all orchestration decisions"""
    __tablename__ = "orchestration_decisions"
    
    decision_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(36), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False, index=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    channel = Column(String(50), nullable=False, index=True)
    consistency_score = Column(Float, nullable=False, index=True)
    latency_ms = Column(Integer, nullable=False)
    constraint_violations = Column(Text, nullable=True)  # JSON string
    reasoning = Column(Text, nullable=False)
    lsmith_trace_id = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("channel IN ('web', 'mobile', 'email', 'multi_channel')"),
        Index("idx_orchestration_customer_timestamp", "customer_id", "timestamp"),
    )
    
    # Relationships
    customer = relationship("Customer", back_populates="orchestration_decisions")
    recommendation_logs = relationship("RecommendationLog", back_populates="orchestration_decision", cascade="all, delete-orphan")
    inventory_audits = relationship("InventoryAudit", back_populates="orchestration_decision")
    
    def __repr__(self):
        return f"<OrchestrationDecision(decision_id={self.decision_id}, customer_id={self.customer_id}, channel={self.channel}, consistency={self.consistency_score})>"


# ============================================================
# 7. RECOMMENDATION LOG MODEL
# ============================================================
class RecommendationLog(Base):
    """Detailed log of each recommendation"""
    __tablename__ = "recommendation_logs"
    
    recommendation_id = Column(Integer, primary_key=True, autoincrement=True)
    decision_id = Column(String(36), ForeignKey("orchestration_decisions.decision_id", ondelete="CASCADE"), nullable=False, index=True)
    
    channel = Column(String(50), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.product_id", ondelete="SET NULL"), nullable=True, index=True)
    confidence = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=False)
    status = Column(String(50), default="approved", nullable=False, index=True)
    status_reason = Column(String(255), nullable=True)
    
    shown_to_customer = Column(Boolean, default=False)
    shown_at = Column(DateTime, nullable=True)
    customer_interaction = Column(String(50), nullable=True, index=True)
    interaction_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('approved', 'modified', 'denied', 'fallback')"),
        CheckConstraint("customer_interaction IN ('click', 'purchase', 'ignore', 'dismiss', NULL)"),
    )
    
    # Relationships
    orchestration_decision = relationship("OrchestrationDecision", back_populates="recommendation_logs")
    product = relationship("Product", back_populates="recommendation_logs")
    
    def __repr__(self):
        return f"<RecommendationLog(recommendation_id={self.recommendation_id}, product_id={self.product_id}, status={self.status})>"


# ============================================================
# 8. CUSTOMER EVENT MODEL
# ============================================================
class CustomerEvent(Base):
    """Customer interaction events"""
    __tablename__ = "customer_events"
    
    event_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(36), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False, index=True)
    
    event_type = Column(String(50), nullable=False, index=True)
    channel = Column(String(50), nullable=True, index=True)
    product_id = Column(String(36), ForeignKey("products.product_id", ondelete="SET NULL"), nullable=True)
    event_data = Column(Text, nullable=True)  # JSON string
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("event_type IN ('page_view', 'product_view', 'click', 'add_to_cart', 'purchase', 'email_open', 'email_click', 'app_open', 'app_tap', 'notification_click', 'wishlist_add')"),
        Index("idx_events_customer_timestamp", "customer_id", "timestamp"),
    )
    
    # Relationships
    customer = relationship("Customer", back_populates="events")
    
    def __repr__(self):
        return f"<CustomerEvent(event_id={self.event_id}, event_type={self.event_type}, customer_id={self.customer_id})>"


# ============================================================
# 9. BUDGET TRACKER MODEL
# ============================================================
class BudgetTracker(Base):
    """Daily email budget tracking"""
    __tablename__ = "budget_tracker"
    
    budget_id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), unique=True, nullable=False, index=True)  # YYYY-MM-DD format
    
    daily_limit = Column(Float, default=1000.00, nullable=False)
    spent_today = Column(Float, default=0.00, nullable=False)
    remaining = Column(Float, default=1000.00, nullable=False)
    
    num_emails_sent = Column(Integer, default=0, nullable=False)
    max_emails_per_day = Column(Integer, default=6666)
    cost_per_email = Column(Float, default=0.15)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<BudgetTracker(date={self.date}, spent={self.spent_today}, remaining={self.remaining})>"


# ============================================================
# 10. INVENTORY AUDIT MODEL
# ============================================================
class InventoryAudit(Base):
    """Inventory change audit trail"""
    __tablename__ = "inventory_audit"
    
    audit_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(36), ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False, index=True)
    
    inventory_before = Column(Integer, nullable=False)
    inventory_after = Column(Integer, nullable=False)
    change_reason = Column(String(100), nullable=False, index=True)
    
    related_decision_id = Column(String(36), ForeignKey("orchestration_decisions.decision_id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("change_reason IN ('purchase', 'restock', 'adjustment', 'conflict_resolution', 'orchestration_allocation', 'return', 'damage', 'correction')"),
    )
    
    # Relationships
    product = relationship("Product", back_populates="inventory_audits")
    orchestration_decision = relationship("OrchestrationDecision", back_populates="inventory_audits")
    
    def __repr__(self):
        return f"<InventoryAudit(product_id={self.product_id}, before={self.inventory_before}, after={self.inventory_after})>"