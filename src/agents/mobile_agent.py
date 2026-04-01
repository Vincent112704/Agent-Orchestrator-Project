from src.agents.base_agent import BaseAgent
from typing import Dict, List
import time
import logging

logging.basicConfig(level=logging.INFO)


class MobileAgent(BaseAgent):
    """
    Mobile Personalization Specialist Agent
    
    Recommends products for customers on mobile apps.
    Optimized for push notifications and in-app experiences.
    Considers device constraints, notification fatigue, and mobile engagement.
    """
    
    def __init__(self):
        """Initialize Mobile Agent"""
        super().__init__(name="MobileAgent", model="gpt-4o-mini")
    
    def recommend(
        self,
        customer_profile: Dict,
        mobile_context: Dict,
        available_products: List[Dict]
    ) -> Dict:
        """
        Generate mobile recommendations for a customer
        
        Args:
            customer_profile: Customer data with affinities
                {
                    "customer_id": str,
                    "segment": str,
                    "mobile_engagement": float,
                    "product_affinities": dict,
                    "recency_days": int,
                    "frequency": int,
                    "monetary": float,
                    "push_notification_count": int,
                    "last_push_timestamp": str
                }
            mobile_context: Current mobile context
                {
                    "app_version": str,
                    "device_type": str (iOS/Android),
                    "os_version": str,
                    "app_section": str,
                    "session_id": str,
                    "notification_preference": str (high/medium/low)
                }
            available_products: List of available products
                [
                    {
                        "product_id": str,
                        "name": str,
                        "category": str,
                        "price": float,
                        "inventory": int,
                        "rating": float,
                        "mobile_friendly": bool
                    },
                    ...
                ]
        
        Returns:
            Dictionary with recommendations
            {
                "recommendations": [
                    {
                        "product_id": str,
                        "confidence": float,
                        "reasoning": str,
                        "notification_title": str,
                        "notification_body": str,
                        "deep_link": str
                    },
                    ...
                ],
                "notification_strategy": str (push/in_app/silent),
                "latency_ms": int,
                "error": str (if error)
            }
        """
        start_time = time.time()
        
        # Format customer affinities
        affinities = customer_profile.get("product_affinities", {})
        affinities_str = "\n".join(
            f"  - {cat}: {score}" for cat, score in affinities.items()
        ) if affinities else "  No affinities recorded"
        
        # Format available products (mobile-optimized)
        mobile_products = [p for p in available_products if p.get("mobile_friendly", True)]
        products_str = "\n".join(
            f"  - {p['product_id']}: {p['name']} (${p['price']}, Rating: {p['rating']}, Stock: {p['inventory']})"
            for p in mobile_products[:8]  # Limit to 8 for mobile context
        )
        
        # Create system prompt
        system_prompt = self.get_prompt_from_file("mobile_agent_prompt.txt")
        logging.info(f"✅ Loaded system prompt for MobileAgent: {len(system_prompt)} characters")
        
        # Create user prompt
        user_prompt = f"""
            Customer Profile:
            - Segment: {customer_profile.get('segment', 'unknown')}
            - Mobile Engagement: {customer_profile.get('mobile_engagement', 0.5)}
            - Recency (days): {customer_profile.get('recency_days', 999)}
            - Frequency: {customer_profile.get('frequency', 0)} purchases
            - Monetary Value: ${customer_profile.get('monetary', 0)}
            - Recent Push Notifications: {customer_profile.get('push_notification_count', 0)}

            Product Affinities:
            {affinities_str}

            Mobile Context:
            - App Section: {mobile_context.get('app_section', 'home')}
            - Device Type: {mobile_context.get('device_type', 'iOS')}
            - OS Version: {mobile_context.get('os_version', 'latest')}
            - Notification Preference: {mobile_context.get('notification_preference', 'medium')}

            Available Mobile-Friendly Products:
            {products_str}

            Task: Recommend 2-4 products optimized for mobile push notifications and in-app display.
            
            Consider:
            - Notification fatigue (avoid if push_notification_count > 5 today)
            - Mobile-friendly product descriptions (short, punchy)
            - Deep linking for seamless navigation
            - Respect notification preference settings

            Return JSON in this format (ONLY JSON, no other text):
            {{
            "recommendations": [
                {{
                "product_id": "PROD_XXX",
                "confidence": 0.95,
                "reasoning": "Why this product is perfect for mobile",
                "notification_title": "Short catchy title",
                "notification_body": "Brief engaging message (max 50 chars)",
                "deep_link": "app://products/PROD_XXX"
                }}
            ],
            "notification_strategy": "push|in_app|silent"
            }}
            """
        
        # Call LLM (LangSmith tracing is automatic)
        result = self.call_llm(system_prompt, user_prompt)
        
        # Calculate total latency
        latency_ms = int((time.time() - start_time) * 1000)
        result["latency_ms"] = latency_ms
        
        # Log trace
        self.log_trace(
            agent_name="MobileAgent",
            inputs={
                "customer_id": customer_profile.get("customer_id"),
                "app_section": mobile_context.get("app_section"),
                "device_type": mobile_context.get("device_type")
            },
            outputs=result,
            latency_ms=latency_ms
        )
        
        return result