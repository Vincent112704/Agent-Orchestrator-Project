from src.agents.base_agent import BaseAgent
from typing import Dict, List
import time
import logging
from src.utils.path import get_project_root

logging.basicConfig(level=logging.INFO)



class WebAgent(BaseAgent):
    """
    Web Personalization Specialist Agent
    
    Recommends products for customers browsing the website.
    Considers customer profile, page context, and available products.
    """
    
    def __init__(self):
        """Initialize Web Agent"""
        super().__init__(name="WebAgent", model="gpt-4o-mini")
    
    def recommend(
        self,
        customer_profile: Dict,
        page_context: Dict,
        available_products: List[Dict]
    ) -> Dict:
        """
        Generate web recommendations for a customer
        
        Args:
            customer_profile: Customer data with affinities
                {
                    "customer_id": str,
                    "segment": str,
                    "web_engagement": float,
                    "product_affinities": dict,
                    "recency_days": int,
                    "frequency": int,
                    "monetary": float
                }
            page_context: Current page context
                {
                    "page": str,
                    "device": str,
                    "session_id": str
                }
            available_products: List of available products
                [
                    {
                        "product_id": str,
                        "name": str,
                        "category": str,
                        "price": float,
                        "inventory": int,
                        "rating": float
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
                        "reasoning": str
                    },
                    ...
                ],
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
            for p in available_products[:10]  # Limit to 10 for context
        )
        
        # Create system prompt
        system_prompt = self.get_prompt_from_file("web_agent_prompt.txt")
        logging.info(f"✅ Loaded system prompt for WebAgent: {len(system_prompt)} characters")
        
        
        # Create user prompt
        user_prompt = f"""
            Customer Profile:
            - Segment: {customer_profile.get('segment', 'unknown')}
            - Web Engagement: {customer_profile.get('web_engagement', 0.5)}
            - Recency (days): {customer_profile.get('recency_days', 999)}
            - Frequency: {customer_profile.get('frequency', 0)} purchases
            - Monetary Value: ${customer_profile.get('monetary', 0)}

            Product Affinities:
            {affinities_str}

            Page Context:
            - Current Page: {page_context.get('page', 'unknown')}
            - Device: {page_context.get('device', 'desktop')}

            Available Products:
            {products_str}

            Task: Recommend 3-5 products that match this customer's interests and the current page context.

            Return JSON in this format (ONLY JSON, no other text):
            {{
            "recommendations": [
                {{
                "product_id": "PROD_XXX",
                "confidence": 0.95,
                "reasoning": "Why this product matches the customer"
                }}
            ]
            }}
            """
        
        # Call LLM (LangSmith tracing is automatic)
        result = self.call_llm(system_prompt, user_prompt)
        
        # Calculate total latency
        latency_ms = int((time.time() - start_time) * 1000)
        result["latency_ms"] = latency_ms
        
        # Log trace
        self.log_trace(
            agent_name="WebAgent",
            inputs={
                "customer_id": customer_profile.get("customer_id"),
                "page": page_context.get("page")
            },
            outputs=result,
            latency_ms=latency_ms
        )
        
        return result
    
