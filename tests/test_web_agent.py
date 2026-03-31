# tests/test_web_agent.py

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.web_agent import WebAgent

def test_web_agent():
    """Test Web Agent with sample data"""
    
    print("\n" + "="*70)
    print("TESTING WEB AGENT WITH LANGSMITH TRACING")
    print("="*70 + "\n")
    
    # Sample customer profile
    customer_profile = {
        "customer_id": "CUST_001",
        "segment": "high_value",
        "web_engagement": 0.92,
        "recency_days": 2,
        "frequency": 15,
        "monetary": 1200.50,
        "product_affinities": {
            "lipstick": 0.95,
            "eyeshadow": 0.72,
            "skincare": 0.35
        }
    }
    
    # Sample page context
    page_context = {
        "page": "category:lipsticks",
        "device": "desktop",
        "session_id": "SESSION_XYZ"
    }
    
    # Sample available products
    available_products = [
        {
            "product_id": "PROD_001",
            "name": "MAC Red Lipstick",
            "category": "lipstick",
            "price": 40.00,
            "inventory": 50,
            "rating": 4.8
        },
        {
            "product_id": "PROD_002",
            "name": "Revlon Red Lipstick",
            "category": "lipstick",
            "price": 28.00,
            "inventory": 120,
            "rating": 4.5
        },
        {
            "product_id": "PROD_003",
            "name": "Red Lip Liner",
            "category": "lip_liner",
            "price": 20.00,
            "inventory": 80,
            "rating": 4.6
        },
        {
            "product_id": "PROD_004",
            "name": "Urban Decay Eyeshadow",
            "category": "eyeshadow",
            "price": 65.00,
            "inventory": 30,
            "rating": 4.9
        },
        {
            "product_id": "PROD_005",
            "name": "CeraVe Moisturizer",
            "category": "skincare",
            "price": 18.00,
            "inventory": 200,
            "rating": 4.7
        }
    ]
    
    print("✓ Step 1: Initializing WebAgent...")
    try:
        agent = WebAgent()
        print("  ✅ WebAgent initialized successfully\n")
    except Exception as e:
        print(f"  ❌ Failed to initialize: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    
    print("✓ Step 2: Generating recommendations...")
    print(f"  Customer: {customer_profile['customer_id']}")
    print(f"  Segment: {customer_profile['segment']}")
    print(f"  Page: {page_context['page']}")
    print(f"  Device: {page_context['device']}\n")
    
    try:
        # Call agent to generate recommendations
        print("  Calling OpenAI API (this may take a few seconds)...\n")
        result = agent.recommend(
            customer_profile=customer_profile,
            page_context=page_context,
            available_products=available_products
        )
        
        # Check for errors
        if "error" in result and result.get("error"):
            print(f"  ❌ Agent returned error: {result['error']}\n")
            if "json_error" in result:
                print(f"  JSON Error Details: {result['json_error']}\n")
            return False
        
        # Display results
        print("  ✅ Recommendations generated successfully!\n")
        
        recommendations = result.get("recommendations", [])
        
        if not recommendations:
            print("  ⚠️  No recommendations returned\n")
        else:
            print(f"  Generated {len(recommendations)} recommendation(s):\n")
            
            for i, rec in enumerate(recommendations, 1):
                product_id = rec.get("product_id", "UNKNOWN")
                confidence = rec.get("confidence", 0)
                reasoning = rec.get("reasoning", "No reasoning provided")
                
                # Find product details
                product = next((p for p in available_products if p["product_id"] == product_id), None)
                product_name = product["name"] if product else "Unknown Product"
                
                print(f"  {i}. {product_id}: {product_name}")
                print(f"     Confidence: {confidence:.2f}")
                print(f"     Reasoning: {reasoning[:100]}{'...' if len(reasoning) > 100 else ''}\n")
        
        # Display metadata
        latency_ms = result.get("latency_ms", 0)
        print(f"  ⏱️  Total Latency: {latency_ms}ms")
        
        # LangSmith info
        print(f"\n  ✅ LangSmith Tracing Active!")
        print(f"     This request has been traced and logged.")
        print(f"     View traces at: https://smith.langchain.com/\n")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error calling agent: {e}\n")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n")
    success = test_web_agent()
    
    print("="*70)
    if success:
        print("✅ WEB AGENT TEST PASSED!")
        print("="*70)
        print("\nNext steps:")
        print("  1. Check LangSmith dashboard for traces")
        print("  2. Create mobile_agent_system.txt and test MobileAgent")
        print("  3. Create email_agent_system.txt and test EmailAgent")
        print("  4. Create coordinator agent and test orchestration")
    else:
        print("❌ WEB AGENT TEST FAILED!")
        print("="*70)
        print("\nTroubleshooting:")
        print("  1. Check your .env file has OPENAI_API_KEY")
        print("  2. Make sure src/prompts/web_agent_system.txt exists")
        print("  3. Check internet connection for OpenAI API")
        print("  4. Verify LANGSMITH_API_KEY is set (for tracing)")
    
    print("="*70 + "\n")
    
    sys.exit(0 if success else 1)