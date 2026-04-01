from src.agents.base_agent import BaseAgent
from typing import Dict, List
import time
import logging

logging.basicConfig(level=logging.INFO)


class EmailAgent(BaseAgent):
    """
    Email Personalization Specialist Agent
    
    Recommends products for email campaigns and digests.
    Optimized for email marketing campaigns, transactional emails, and digests.
    Considers email fatigue, segment preferences, and engagement history.
    """
    
    def __init__(self):
        """Initialize Email Agent"""
        super().__init__(name="EmailAgent", model="gpt-4o-mini")
    
    def recommend(
        self,
        customer_profile: Dict,
        email_context: Dict,
        available_products: List[Dict]
    ) -> Dict:
        """
        Generate email recommendations for a customer
        
        Args:
            customer_profile: Customer data with affinities
                {
                    "customer_id": str,
                    "segment": str,
                    "email_engagement": float,
                    "product_affinities": dict,
                    "recency_days": int,
                    "frequency": int,
                    "monetary": float,
                    "email_open_rate": float,
                    "email_click_rate": float,
                    "emails_received_week": int,
                    "unsubscribe_risk": float
                }
            email_context: Current email context
                {
                    "campaign_type": str (promotional/digest/transactional),
                    "email_type": str (newsletter/cart_reminder/order_confirmation),
                    "send_time": str,
                    "campaign_id": str,
                    "segment_id": str
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
                        "email_thumbnail": str (image URL)
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
                        "email_subject_hook": str,
                        "email_description": str,
                        "cta_text": str,
                        "landing_page_url": str
                    },
                    ...
                ],
                "email_strategy": str (aggressive/moderate/conservative),
                "subject_line_suggestion": str,
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
        
        # Format available products
        products_str = "\n".join(
            f"  - {p['product_id']}: {p['name']} (${p['price']}, Rating: {p['rating']}, Stock: {p['inventory']})"
            for p in available_products[:12]  # Limit to 12 for email carousel/grid
        )
        
        # Create system prompt
        system_prompt = self.get_prompt_from_file("email_agent_prompt.txt")
        logging.info(f"✅ Loaded system prompt for EmailAgent: {len(system_prompt)} characters")
        
        # Create user prompt
        user_prompt = f"""
            Customer Profile:
            - Segment: {customer_profile.get('segment', 'unknown')}
            - Email Engagement: {customer_profile.get('email_engagement', 0.5)}
            - Email Open Rate: {customer_profile.get('email_open_rate', 0.3):.2%}
            - Email Click Rate: {customer_profile.get('email_click_rate', 0.05):.2%}
            - Recency (days): {customer_profile.get('recency_days', 999)}
            - Frequency: {customer_profile.get('frequency', 0)} purchases
            - Monetary Value: ${customer_profile.get('monetary', 0)}
            - Emails Received This Week: {customer_profile.get('emails_received_week', 0)}
            - Unsubscribe Risk: {customer_profile.get('unsubscribe_risk', 0.0):.2%}

            Product Affinities:
            {affinities_str}

            Email Context:
            - Campaign Type: {email_context.get('campaign_type', 'promotional')}
            - Email Type: {email_context.get('email_type', 'newsletter')}
            - Campaign ID: {email_context.get('campaign_id', 'unknown')}
            - Segment: {email_context.get('segment_id', 'general')}

            Available Products:
            {products_str}

            Task: Recommend 3-6 products optimized for email marketing.
            
            Consider:
            - Email fatigue (emails_received_week and unsubscribe_risk)
            - Campaign type (promotional vs transactional vs digest)
            - Email open/click history
            - Product diversity within affinities
            - Email best practices (punchy subject hooks, compelling CTAs)

            Return JSON in this format (ONLY JSON, no other text):
            {{
            "recommendations": [
                {{
                "product_id": "PROD_XXX",
                "confidence": 0.95,
                "reasoning": "Why this product resonates with this customer",
                "email_subject_hook": "Hook phrase for subject line (max 20 words)",
                "email_description": "Brief email-friendly description",
                "cta_text": "Call-to-action button text",
                "landing_page_url": "https://shop.com/products/PROD_XXX"
                }}
            ],
            "email_strategy": "aggressive|moderate|conservative",
            "subject_line_suggestion": "Complete subject line (max 50 chars)"
            }}
            """
        
        # Call LLM (LangSmith tracing is automatic)
        result = self.call_llm(system_prompt, user_prompt)
        
        # Calculate total latency
        latency_ms = int((time.time() - start_time) * 1000)
        result["latency_ms"] = latency_ms
        
        # Log trace
        self.log_trace(
            agent_name="EmailAgent",
            inputs={
                "customer_id": customer_profile.get("customer_id"),
                "campaign_type": email_context.get("campaign_type"),
                "email_type": email_context.get("email_type")
            },
            outputs=result,
            latency_ms=latency_ms
        )
        
        return result