from src.agents.base_agent import BaseAgent
from src.agents.web_agent import WebAgent
from src.agents.mobile_agent import MobileAgent
from src.agents.email_agent import EmailAgent
from typing import Dict, List, Optional
import time
import logging
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ConsistencyScore:
    """Measures consistency across channel recommendations"""
    overall_score: float  # 0.0-1.0
    web_mobile_overlap: float  # Shared products between web and mobile
    mobile_email_overlap: float  # Shared products between mobile and email
    web_email_overlap: float  # Shared products between web and email
    triple_overlap: float  # Products recommended across all three channels
    reasoning: str


class Coordinator(BaseAgent):
    """
    Orchestrator Agent - Coordinates Web, Mobile, and Email agents
    
    Ensures consistent, personalized recommendations across all channels
    while respecting channel-specific constraints and optimizations.
    
    Key responsibilities:
    - Call all three specialist agents in parallel
    - Validate recommendations against business constraints
    - Measure consistency across channels (target ≥85%)
    - Coordinate budget and inventory allocation
    - Ensure frequency caps are respected
    - Log orchestration decisions for analysis
    """
    
    def __init__(self):
        """Initialize Coordinator with all specialist agents"""
        super().__init__(name="Coordinator", model="gpt-4o-mini")
        self.web_agent = WebAgent()
        self.mobile_agent = MobileAgent()
        self.email_agent = EmailAgent()
        
        logger.info("✅ Coordinator initialized with Web, Mobile, and Email agents")
    
    def orchestrate(
        self,
        customer_profile: Dict,
        page_context: Dict,
        mobile_context: Dict,
        email_context: Dict,
        available_products: List[Dict],
        budget_constraint: Optional[float] = None,
        inventory_constraint: Optional[Dict] = None,
        frequency_cap: Optional[Dict] = None
    ) -> Dict:
        """
        Orchestrate recommendations across all three channels
        
        Args:
            customer_profile: Complete customer data
                {
                    "customer_id": str,
                    "segment": str,
                    "web_engagement": float,
                    "mobile_engagement": float,
                    "email_engagement": float,
                    "product_affinities": dict,
                    "recency_days": int,
                    "frequency": int,
                    "monetary": float,
                    "push_notification_count": int,
                    "emails_received_week": int,
                    "unsubscribe_risk": float
                }
            page_context: Web channel context
            mobile_context: Mobile channel context
            email_context: Email channel context
            available_products: List of available products
            budget_constraint: Max spend per customer (optional)
            inventory_constraint: Inventory limits by product (optional)
            frequency_cap: Max recommendations per channel per day (optional)
        
        Returns:
            {
                "web_recommendations": [...],
                "mobile_recommendations": [...],
                "email_recommendations": [...],
                "consistency_score": ConsistencyScore,
                "orchestration_decision": str,
                "constraint_violations": [...],
                "total_latency_ms": int,
                "error": str (if error)
            }
        """
        start_time = time.time()
        constraint_violations = []
        
        try:
            logger.info(f"🎯 Starting orchestration for customer: {customer_profile.get('customer_id')}")
            
            # Call all three agents in parallel (conceptually)
            logger.info("📱 Calling Web Agent...")
            web_result = self.web_agent.recommend(
                customer_profile=customer_profile,
                page_context=page_context,
                available_products=available_products
            )
            
            logger.info("📲 Calling Mobile Agent...")
            mobile_result = self.mobile_agent.recommend(
                customer_profile=customer_profile,
                mobile_context=mobile_context,
                available_products=available_products
            )
            
            logger.info("📧 Calling Email Agent...")
            email_result = self.email_agent.recommend(
                customer_profile=customer_profile,
                email_context=email_context,
                available_products=available_products
            )
            
            # Validate constraints
            if frequency_cap:
                violations = self._validate_frequency_cap(
                    web_result, mobile_result, email_result, frequency_cap
                )
                constraint_violations.extend(violations)
            
            if budget_constraint:
                violations = self._validate_budget(
                    web_result, mobile_result, email_result, 
                    available_products, budget_constraint
                )
                constraint_violations.extend(violations)
            
            if inventory_constraint:
                violations = self._validate_inventory(
                    web_result, mobile_result, email_result,
                    available_products, inventory_constraint
                )
                constraint_violations.extend(violations)
            
            # Calculate consistency score
            consistency_score = self._calculate_consistency(
                web_result, mobile_result, email_result
            )
            
            # Determine orchestration strategy
            orchestration_decision = self._make_orchestration_decision(
                web_result, mobile_result, email_result,
                consistency_score, constraint_violations,
                customer_profile
            )
            
            # Calculate total latency
            total_latency_ms = int((time.time() - start_time) * 1000)
            
            # Log orchestration trace
            self.log_trace(
                agent_name="Coordinator",
                inputs={
                    "customer_id": customer_profile.get("customer_id"),
                    "segment": customer_profile.get("segment"),
                    "channels": ["web", "mobile", "email"]
                },
                outputs={
                    "consistency_score": consistency_score.overall_score,
                    "constraint_violations": len(constraint_violations),
                    "orchestration_decision": orchestration_decision
                },
                latency_ms=total_latency_ms
            )
            
            logger.info(
                f"✅ Orchestration complete | "
                f"Consistency: {consistency_score.overall_score:.2%} | "
                f"Violations: {len(constraint_violations)} | "
                f"Latency: {total_latency_ms}ms"
            )
            
            return {
                "web_recommendations": web_result.get("recommendations", []),
                "mobile_recommendations": mobile_result.get("recommendations", []),
                "email_recommendations": email_result.get("recommendations", []),
                "consistency_score": {
                    "overall_score": consistency_score.overall_score,
                    "web_mobile_overlap": consistency_score.web_mobile_overlap,
                    "mobile_email_overlap": consistency_score.mobile_email_overlap,
                    "web_email_overlap": consistency_score.web_email_overlap,
                    "triple_overlap": consistency_score.triple_overlap,
                    "reasoning": consistency_score.reasoning
                },
                "orchestration_decision": orchestration_decision,
                "constraint_violations": constraint_violations,
                "web_latency_ms": web_result.get("latency_ms", 0),
                "mobile_latency_ms": mobile_result.get("latency_ms", 0),
                "email_latency_ms": email_result.get("latency_ms", 0),
                "total_latency_ms": total_latency_ms,
                "error": None
            }
        
        except Exception as e:
            logger.error(f"❌ Orchestration failed: {str(e)}")
            total_latency_ms = int((time.time() - start_time) * 1000)
            return {
                "web_recommendations": [],
                "mobile_recommendations": [],
                "email_recommendations": [],
                "consistency_score": None,
                "orchestration_decision": None,
                "constraint_violations": constraint_violations,
                "total_latency_ms": total_latency_ms,
                "error": str(e)
            }
    
    def _calculate_consistency(
        self,
        web_result: Dict,
        mobile_result: Dict,
        email_result: Dict
    ) -> ConsistencyScore:
        """Calculate consistency score across channels"""
        
        # Extract product IDs from recommendations
        web_prods = set(r.get("product_id") for r in web_result.get("recommendations", []))
        mobile_prods = set(r.get("product_id") for r in mobile_result.get("recommendations", []))
        email_prods = set(r.get("product_id") for r in email_result.get("recommendations", []))
        
        # Calculate overlaps
        web_mobile_overlap = len(web_prods & mobile_prods) / max(len(web_prods | mobile_prods), 1)
        mobile_email_overlap = len(mobile_prods & email_prods) / max(len(mobile_prods | email_prods), 1)
        web_email_overlap = len(web_prods & email_prods) / max(len(web_prods | email_prods), 1)
        triple_overlap = len(web_prods & mobile_prods & email_prods) / max(len(web_prods | mobile_prods | email_prods), 1)
        
        # Overall consistency (weighted average)
        overall_score = (
            web_mobile_overlap * 0.35 +
            mobile_email_overlap * 0.35 +
            web_email_overlap * 0.20 +
            triple_overlap * 0.10
        )
        
        reasoning = (
            f"Web-Mobile: {web_mobile_overlap:.0%}, "
            f"Mobile-Email: {mobile_email_overlap:.0%}, "
            f"Web-Email: {web_email_overlap:.0%}, "
            f"Triple: {triple_overlap:.0%}"
        )
        
        return ConsistencyScore(
            overall_score=overall_score,
            web_mobile_overlap=web_mobile_overlap,
            mobile_email_overlap=mobile_email_overlap,
            web_email_overlap=web_email_overlap,
            triple_overlap=triple_overlap,
            reasoning=reasoning
        )
    
    def _validate_frequency_cap(
        self,
        web_result: Dict,
        mobile_result: Dict,
        email_result: Dict,
        frequency_cap: Dict
    ) -> List[str]:
        """Validate frequency caps per channel"""
        violations = []
        
        web_count = len(web_result.get("recommendations", []))
        mobile_count = len(mobile_result.get("recommendations", []))
        email_count = len(email_result.get("recommendations", []))
        
        if web_count > frequency_cap.get("web", 5):
            violations.append(f"Web: {web_count} exceeds cap of {frequency_cap.get('web', 5)}")
        
        if mobile_count > frequency_cap.get("mobile", 4):
            violations.append(f"Mobile: {mobile_count} exceeds cap of {frequency_cap.get('mobile', 4)}")
        
        if email_count > frequency_cap.get("email", 6):
            violations.append(f"Email: {email_count} exceeds cap of {frequency_cap.get('email', 6)}")
        
        return violations
    
    def _validate_budget(
        self,
        web_result: Dict,
        mobile_result: Dict,
        email_result: Dict,
        available_products: List[Dict],
        budget_constraint: float
    ) -> List[str]:
        """Validate total spend across channels"""
        violations = []
        
        product_map = {p["product_id"]: p for p in available_products}
        total_spend = 0
        
        for rec in web_result.get("recommendations", []) + \
                   mobile_result.get("recommendations", []) + \
                   email_result.get("recommendations", []):
            product = product_map.get(rec.get("product_id"), {})
            total_spend += product.get("price", 0)
        
        if total_spend > budget_constraint:
            violations.append(f"Budget: ${total_spend:.2f} exceeds ${budget_constraint:.2f}")
        
        return violations
    
    def _validate_inventory(
        self,
        web_result: Dict,
        mobile_result: Dict,
        email_result: Dict,
        available_products: List[Dict],
        inventory_constraint: Dict
    ) -> List[str]:
        """Validate inventory availability"""
        violations = []
        
        product_map = {p["product_id"]: p for p in available_products}
        product_counts = {}
        
        for rec in web_result.get("recommendations", []) + \
                   mobile_result.get("recommendations", []) + \
                   email_result.get("recommendations", []):
            prod_id = rec.get("product_id")
            product_counts[prod_id] = product_counts.get(prod_id, 0) + 1
        
        for prod_id, count in product_counts.items():
            constraint = inventory_constraint.get(prod_id, float('inf'))
            if count > constraint:
                violations.append(f"Product {prod_id}: recommended {count} times exceeds constraint of {constraint}")
        
        return violations
    
    def _make_orchestration_decision(
        self,
        web_result: Dict,
        mobile_result: Dict,
        email_result: Dict,
        consistency_score: ConsistencyScore,
        constraint_violations: List[str],
        customer_profile: Dict
    ) -> str:
        """Determine final orchestration strategy based on analysis"""
        
        decision_factors = []
        
        # Consistency threshold
        if consistency_score.overall_score >= 0.85:
            decision_factors.append("✅ HIGH_CONSISTENCY")
        elif consistency_score.overall_score >= 0.70:
            decision_factors.append("⚠️ MODERATE_CONSISTENCY")
        else:
            decision_factors.append("⛔ LOW_CONSISTENCY")
        
        # Constraints
        if constraint_violations:
            decision_factors.append(f"⚠️ {len(constraint_violations)}_VIOLATIONS")
        else:
            decision_factors.append("✅ NO_VIOLATIONS")
        
        # Customer segment
        segment = customer_profile.get("segment", "unknown")
        decision_factors.append(f"SEGMENT:{segment}")
        
        # Engagement level
        avg_engagement = (
            customer_profile.get("web_engagement", 0) +
            customer_profile.get("mobile_engagement", 0) +
            customer_profile.get("email_engagement", 0)
        ) / 3
        
        if avg_engagement > 0.7:
            decision_factors.append("HIGH_ENGAGEMENT")
        elif avg_engagement > 0.4:
            decision_factors.append("MEDIUM_ENGAGEMENT")
        else:
            decision_factors.append("LOW_ENGAGEMENT")
        
        return " | ".join(decision_factors)