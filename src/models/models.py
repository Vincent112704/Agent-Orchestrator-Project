"""
SQLAlchemy ORM models for Real-Time Personalization Orchestrator
Maps to database schema for users, customers, products, and orchestration decisions
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User authentication and account info"""
    __tablename__ = "users"

    user_id = Column(String(255), primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="user", uselist=False, cascade="all, delete-orphan")
    events = relationship("CustomerEvent", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, email={self.email})>"


class Customer(Base):
    """Customer profile with RFM metrics and engagement tracking"""
    __tablename__ = "customers"

    customer_id = Column(String(255), primary_key=True, index=True)
    user_id = Column(String(255), ForeignKey("users.user_id"), unique=True, nullable=False, index=True)
    segment = Column(String(50), default="new", nullable=False, index=True)  # new, at_risk, loyal, high_value, vip
    web_engagement = Column(Float, default=0.5)
    mobile_engagement = Column(Float, default=0.5)
    email_engagement = Column(Float, default=0.5)
    email_unsubscribed = Column(Boolean, default=False)
    email_frequency_max_per_week = Column(Integer, default=3)
    email_last_sent_at = Column(DateTime, nullable=True)
    recency_days = Column(Integer, default=999, index=True)  # RFM: days since last purchase
    frequency = Column(Integer, default=0)  # RFM: purchase count
    frequency_period = Column(String(50), default="90_days")  # Time period for frequency
    monetary = Column(Float, default=0.0, index=True)  # RFM: total spend
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="customer")
    affinities = relationship("CustomerAffinity", back_populates="customer", cascade="all, delete-orphan")
    customer_products = relationship("CustomerProduct", back_populates="customer", cascade="all, delete-orphan")
    orchestration_decisions = relationship("OrchestrationDecision", back_populates="customer", cascade="all, delete-orphan")
    events = relationship("CustomerEvent", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Customer(customer_id={self.customer_id}, segment={self.segment}, monetary={self.monetary})>"


class CustomerAffinity(Base):
    """Customer affinity scores for product categories"""
    __tablename__ = "customer_affinities"

    affinity_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(255), ForeignKey("customers.customer_id"), nullable=False, index=True)
    category = Column(String(255), nullable=False, index=True)
    affinity_score = Column(Float, nullable=False)  # 0.0 to 1.0
    updated_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="affinities")

    __table_args__ = (
        # Unique constraint on customer_id + category
        {"uniqueConstraint": True},
    )

    def __repr__(self):
        return f"<CustomerAffinity(customer_id={self.customer_id}, category={self.category}, score={self.affinity_score})>"


class Product(Base):
    """Product catalog with inventory and metadata"""
    __tablename__ = "products"

    product_id = Column(String(255), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(255), nullable=False, index=True)
    price = Column(Float, nullable=False)
    inventory = Column(Integer, default=0, index=True)
    rating = Column(Float, default=0.0)
    description = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer_products = relationship("CustomerProduct", back_populates="product", cascade="all, delete-orphan")
    inventory_audits = relationship("InventoryAudit", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product(product_id={self.product_id}, name={self.name}, inventory={self.inventory})>"


class CustomerProduct(Base):
    """Customer interactions with products (views, clicks, purchases, etc.)"""
    __tablename__ = "customer_products"

    customer_product_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(255), ForeignKey("customers.customer_id"), nullable=False, index=True)
    product_id = Column(String(255), ForeignKey("products.product_id"), nullable=False, index=True)
    interaction_type = Column(String(50), nullable=False, index=True)  # view, click, add_to_cart, purchase, wishlist, email_open, email_click, recommendation_shown
    interaction_count = Column(Integer, default=1)
    last_interaction_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="customer_products")
    product = relationship("Product", back_populates="customer_products")

    def __repr__(self):
        return f"<CustomerProduct(customer_id={self.customer_id}, product_id={self.product_id}, interaction={self.interaction_type})>"


class OrchestrationDecision(Base):
    """Orchestration decisions made by the multi-agent system"""
    __tablename__ = "orchestration_decisions"

    decision_id = Column(String(255), primary_key=True, index=True)
    customer_id = Column(String(255), ForeignKey("customers.customer_id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    channel = Column(String(50), nullable=False, index=True)  # web, mobile, email, multi_channel
    consistency_score = Column(Float, nullable=False)  # 0.0 to 1.0
    latency_ms = Column(Integer, nullable=False)
    constraint_violations = Column(Text, nullable=True)  # JSON or comma-separated violations
    reasoning = Column(Text, nullable=False)  # Why this decision was made
    lsmith_trace_id = Column(String(255), nullable=True)  # LangSmith trace ID for debugging
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    customer = relationship("Customer", back_populates="orchestration_decisions")
    recommendation_logs = relationship("RecommendationLog", back_populates="orchestration_decision", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<OrchestrationDecision(decision_id={self.decision_id}, customer_id={self.customer_id}, channel={self.channel})>"


class RecommendationLog(Base):
    """Individual recommendations within an orchestration decision"""
    __tablename__ = "recommendation_logs"

    recommendation_id = Column(Integer, primary_key=True, autoincrement=True)
    decision_id = Column(String(255), ForeignKey("orchestration_decisions.decision_id"), nullable=False, index=True)
    channel = Column(String(50), nullable=False, index=True)
    product_id = Column(String(255), ForeignKey("products.product_id"), nullable=True, index=True)
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    reasoning = Column(Text, nullable=False)
    status = Column(String(50), default="approved", nullable=False, index=True)  # approved, modified, denied, fallback
    status_reason = Column(Text, nullable=True)
    shown_to_customer = Column(Boolean, default=False)
    shown_at = Column(DateTime, nullable=True)
    customer_interaction = Column(String(50), nullable=True, index=True)  # click, purchase, ignore, dismiss
    interaction_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    orchestration_decision = relationship("OrchestrationDecision", back_populates="recommendation_logs")

    def __repr__(self):
        return f"<RecommendationLog(recommendation_id={self.recommendation_id}, decision_id={self.decision_id}, status={self.status})>"


class CustomerEvent(Base):
    """Customer events across all channels"""
    __tablename__ = "customer_events"

    event_id = Column(String(255), primary_key=True, index=True)
    customer_id = Column(String(255), ForeignKey("customers.customer_id"), nullable=False, index=True)
    user_id = Column(String(255), ForeignKey("users.user_id"), nullable=False)
    event_type = Column(String(100), nullable=False, index=True)  # page_view, product_view, click, add_to_cart, purchase, email_open, email_click, app_open, app_tap, notification_click, wishlist_add
    channel = Column(String(50), nullable=True, index=True)  # web, mobile, email
    product_id = Column(String(255), ForeignKey("products.product_id"), nullable=True, index=True)
    event_data = Column(Text, nullable=True)  # JSON string with event details
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="events")
    user = relationship("User", back_populates="events")

    def __repr__(self):
        return f"<CustomerEvent(event_id={self.event_id}, customer_id={self.customer_id}, event_type={self.event_type})>"


class BudgetTracker(Base):
    """Daily budget tracking for marketing spend"""
    __tablename__ = "budget_tracker"

    budget_id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, unique=True, nullable=False, index=True)
    daily_limit = Column(Float, default=1000.0, nullable=False)
    spent_today = Column(Float, default=0.0, nullable=False)
    remaining = Column(Float, default=1000.0, nullable=False)
    num_emails_sent = Column(Integer, default=0, nullable=False)
    max_emails_per_day = Column(Integer, default=6666)
    cost_per_email = Column(Float, default=0.15)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<BudgetTracker(date={self.date}, remaining={self.remaining}, emails_sent={self.num_emails_sent})>"


class InventoryAudit(Base):
    """Audit log for inventory changes"""
    __tablename__ = "inventory_audit"

    audit_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(255), ForeignKey("products.product_id"), nullable=False, index=True)
    inventory_before = Column(Integer, nullable=False)
    inventory_after = Column(Integer, nullable=False)
    change_reason = Column(String(100), nullable=False, index=True)  # purchase, restock, adjustment, conflict_resolution, orchestration_allocation, return, damage, correction
    related_decision_id = Column(String(255), ForeignKey("orchestration_decisions.decision_id"), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="inventory_audits")

    def __repr__(self):
        return f"<InventoryAudit(product_id={self.product_id}, change={self.inventory_after - self.inventory_before})>"