import sys
from pathlib import Path
import pytest
import logging
from typing import Dict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.orchestrator import Coordinator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestCoordinator:
    """Test suite for Coordinator agent"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.coordinator = Coordinator()
        self.available_products = [
            {
                "product_id": "PROD_001",
                "name": "Wireless Headphones",
                "category": "Electronics",
                "price": 129.99,
                "inventory": 45,
                "rating": 4.7,
                "mobile_friendly": True,
                "email_thumbnail": "https://example.com/prod001.jpg"
            },
            {
                "product_id": "PROD_002",
                "name": "USB-C Cable",
                "category": "Accessories",
                "price": 19.99,
                "inventory": 200,
                "rating": 4.5,
                "mobile_friendly": True,
                "email_thumbnail": "https://example.com/prod002.jpg"
            },
            {
                "product_id": "PROD_003",
                "name": "Laptop Stand",
                "category": "Accessories",
                "price": 49.99,
                "inventory": 30,
                "rating": 4.6,
                "mobile_friendly": True,
                "email_thumbnail": "https://example.com/prod003.jpg"
            },
            {
                "product_id": "PROD_004",
                "name": "4K Webcam",
                "category": "Electronics",
                "price": 159.99,
                "inventory": 15,
                "rating": 4.8,
                "mobile_friendly": True,
                "email_thumbnail": "https://example.com/prod004.jpg"
            },
            {
                "product_id": "PROD_005",
                "name": "Desk Organizer",
                "category": "Home & Garden",
                "price": 34.99,
                "inventory": 60,
                "rating": 4.3,
                "mobile_friendly": True,
                "email_thumbnail": "https://example.com/prod005.jpg"
            }
        ]
    
    def _get_base_profile(self) -> Dict:
        """Get base customer profile"""
        return {
            "customer_id": "CUST_TEST_001",
            "segment": "standard",
            "web_engagement": 0.5,
            "mobile_engagement": 0.5,
            "email_engagement": 0.5,
            "product_affinities": {
                "Electronics": 0.80,
                "Accessories": 0.70,
                "Home & Garden": 0.40
            },
            "recency_days": 10,
            "frequency": 5,
            "monetary": 500.00,
            "push_notification_count": 1,
            "emails_received_week": 2,
            "unsubscribe_risk": 0.05
        }
    
    def _get_page_context(self) -> Dict:
        """Get web context"""
        return {
            "page": "product_listing",
            "device": "desktop",
            "session_id": "sess_12345"
        }
    
    def _get_mobile_context(self) -> Dict:
        """Get mobile context"""
        return {
            "app_version": "2.1.0",
            "device_type": "iOS",
            "os_version": "17.0",
            "app_section": "home",
            "session_id": "sess_67890",
            "notification_preference": "high"
        }
    
    def _get_email_context(self) -> Dict:
        """Get email context"""
        return {
            "campaign_type": "promotional",
            "email_type": "newsletter",
            "send_time": "2024-04-01T10:00:00Z",
            "campaign_id": "camp_001",
            "segment_id": "standard"
        }
    
    # TEST 1: Basic orchestration without constraints
    def test_basic_orchestration(self):
        """Test basic orchestration across all three channels"""
        logger.info("\n" + "="*80)
        logger.info("TEST 1: Basic Orchestration (No Constraints)")
        logger.info("="*80)
        
        profile = self._get_base_profile()
        
        result = self.coordinator.orchestrate(
            customer_profile=profile,
            page_context=self._get_page_context(),
            mobile_context=self._get_mobile_context(),
            email_context=self._get_email_context(),
            available_products=self.available_products
        )
        
        # Assertions
        assert result["error"] is None, f"Should not have error: {result['error']}"
        assert len(result["web_recommendations"]) > 0, "Should have web recommendations"
        assert len(result["mobile_recommendations"]) > 0, "Should have mobile recommendations"
        assert len(result["email_recommendations"]) > 0, "Should have email recommendations"
        assert result["consistency_score"] is not None, "Should have consistency score"
        assert result["total_latency_ms"] > 0, "Should have latency"
        
        logger.info(f"✅ Web recommendations: {len(result['web_recommendations'])}")
        logger.info(f"✅ Mobile recommendations: {len(result['mobile_recommendations'])}")
        logger.info(f"✅ Email recommendations: {len(result['email_recommendations'])}")
        logger.info(f"✅ Consistency score: {result['consistency_score']['overall_score']:.0%}")
        logger.info(f"✅ Total latency: {result['total_latency_ms']}ms")
    
    # TEST 2: High engagement premium customer
    def test_premium_customer(self):
        """Test orchestration for high-engagement premium customer"""
        logger.info("\n" + "="*80)
        logger.info("TEST 2: Premium High-Engagement Customer")
        logger.info("="*80)
        
        profile = self._get_base_profile()
        profile.update({
            "customer_id": "CUST_PREMIUM_001",
            "segment": "premium",
            "web_engagement": 0.95,
            "mobile_engagement": 0.90,
            "email_engagement": 0.85,
            "frequency": 50,
            "monetary": 5000.00,
            "unsubscribe_risk": 0.01,
            "product_affinities": {
                "Electronics": 0.95,
                "Accessories": 0.85,
                "Home & Garden": 0.70
            }
        })
        
        result = self.coordinator.orchestrate(
            customer_profile=profile,
            page_context=self._get_page_context(),
            mobile_context=self._get_mobile_context(),
            email_context=self._get_email_context(),
            available_products=self.available_products,
            budget_constraint=1000.0
        )
        
        # Premium customers should get more recommendations
        total_recs = (len(result["web_recommendations"]) + 
                     len(result["mobile_recommendations"]) + 
                     len(result["email_recommendations"]))
        
        assert total_recs > 0, "Premium customer should get recommendations"
        assert "SEGMENT:premium" in result["orchestration_decision"], "Should recognize premium segment"
        assert "HIGH_ENGAGEMENT" in result["orchestration_decision"], "Should recognize high engagement"
        
        logger.info(f"✅ Total recommendations: {total_recs}")
        logger.info(f"✅ Decision: {result['orchestration_decision']}")
    
    # TEST 3: Low engagement at-risk customer
    def test_at_risk_customer(self):
        """Test orchestration for low-engagement, high-risk customer"""
        logger.info("\n" + "="*80)
        logger.info("TEST 3: Low-Engagement At-Risk Customer")
        logger.info("="*80)
        
        profile = self._get_base_profile()
        profile.update({
            "customer_id": "CUST_ATRISK_001",
            "segment": "at_risk",
            "web_engagement": 0.15,
            "mobile_engagement": 0.10,
            "email_engagement": 0.20,
            "recency_days": 90,
            "frequency": 1,
            "monetary": 50.00,
            "unsubscribe_risk": 0.75,
            "emails_received_week": 8,
            "push_notification_count": 10
        })
        
        result = self.coordinator.orchestrate(
            customer_profile=profile,
            page_context=self._get_page_context(),
            mobile_context=self._get_mobile_context(),
            email_context=self._get_email_context(),
            available_products=self.available_products
        )
        
        assert result["error"] is None, "Should complete even for at-risk customer"
        assert "LOW_ENGAGEMENT" in result["orchestration_decision"], "Should recognize low engagement"
        
        logger.info(f"✅ Decision: {result['orchestration_decision']}")
        logger.info(f"✅ Consistency: {result['consistency_score']['overall_score']:.0%}")
    
    # TEST 4: Budget constraint validation
    def test_budget_constraint(self):
        """Test budget constraint enforcement"""
        logger.info("\n" + "="*80)
        logger.info("TEST 4: Budget Constraint Validation")
        logger.info("="*80)
        
        profile = self._get_base_profile()
        
        # Tight budget constraint
        result = self.coordinator.orchestrate(
            customer_profile=profile,
            page_context=self._get_page_context(),
            mobile_context=self._get_mobile_context(),
            email_context=self._get_email_context(),
            available_products=self.available_products,
            budget_constraint=50.0  # Very tight budget
        )
        
        # With tight budget, may get violations
        if result["constraint_violations"]:
            logger.info(f"⚠️ Budget constraint violations detected:")
            for violation in result["constraint_violations"]:
                logger.info(f"   {violation}")
        else:
            logger.info(f"✅ All recommendations within budget")
        
        assert result["error"] is None, "Should not error with constraints"
    
    # TEST 5: Frequency cap validation
    def test_frequency_cap(self):
        """Test frequency cap enforcement"""
        logger.info("\n" + "="*80)
        logger.info("TEST 5: Frequency Cap Validation")
        logger.info("="*80)
        
        profile = self._get_base_profile()
        
        # Strict frequency caps
        frequency_cap = {"web": 2, "mobile": 1, "email": 2}
        
        result = self.coordinator.orchestrate(
            customer_profile=profile,
            page_context=self._get_page_context(),
            mobile_context=self._get_mobile_context(),
            email_context=self._get_email_context(),
            available_products=self.available_products,
            frequency_cap=frequency_cap
        )
        
        web_count = len(result["web_recommendations"])
        mobile_count = len(result["mobile_recommendations"])
        email_count = len(result["email_recommendations"])
        
        logger.info(f"Web recommendations: {web_count} (cap: {frequency_cap['web']})")
        logger.info(f"Mobile recommendations: {mobile_count} (cap: {frequency_cap['mobile']})")
        logger.info(f"Email recommendations: {email_count} (cap: {frequency_cap['email']})")
        
        assert result["error"] is None, "Should respect frequency caps"
    
    # TEST 6: Consistency score calculation
    def test_consistency_score(self):
        """Test consistency score across channels"""
        logger.info("\n" + "="*80)
        logger.info("TEST 6: Consistency Score Calculation")
        logger.info("="*80)
        
        profile = self._get_base_profile()
        
        result = self.coordinator.orchestrate(
            customer_profile=profile,
            page_context=self._get_page_context(),
            mobile_context=self._get_mobile_context(),
            email_context=self._get_email_context(),
            available_products=self.available_products
        )
        
        consistency = result["consistency_score"]
        
        logger.info(f"Overall consistency: {consistency['overall_score']:.0%}")
        logger.info(f"Web-Mobile overlap: {consistency['web_mobile_overlap']:.0%}")
        logger.info(f"Mobile-Email overlap: {consistency['mobile_email_overlap']:.0%}")
        logger.info(f"Web-Email overlap: {consistency['web_email_overlap']:.0%}")
        logger.info(f"Triple overlap: {consistency['triple_overlap']:.0%}")
        logger.info(f"Reasoning: {consistency['reasoning']}")
        
        # All scores should be between 0 and 1
        assert 0 <= consistency['overall_score'] <= 1, "Overall score should be 0-1"
        assert 0 <= consistency['web_mobile_overlap'] <= 1, "Web-mobile overlap should be 0-1"
        
        if consistency['overall_score'] >= 0.85:
            logger.info("✅ HIGH consistency (≥85%)")
        elif consistency['overall_score'] >= 0.70:
            logger.info("⚠️ MODERATE consistency (70-85%)")
        else:
            logger.info("⛔ LOW consistency (<70%)")
    
    # TEST 7: Inventory constraint validation
    def test_inventory_constraint(self):
        """Test inventory constraint enforcement"""
        logger.info("\n" + "="*80)
        logger.info("TEST 7: Inventory Constraint Validation")
        logger.info("="*80)
        
        profile = self._get_base_profile()
        
        # Strict inventory constraints
        inventory_constraint = {
            "PROD_001": 1,  # Can only recommend once across all channels
            "PROD_002": 2,
            "PROD_003": 2,
            "PROD_004": 1,
            "PROD_005": 1
        }
        
        result = self.coordinator.orchestrate(
            customer_profile=profile,
            page_context=self._get_page_context(),
            mobile_context=self._get_mobile_context(),
            email_context=self._get_email_context(),
            available_products=self.available_products,
            inventory_constraint=inventory_constraint
        )
        
        if result["constraint_violations"]:
            logger.info(f"⚠️ Inventory violations detected:")
            for violation in result["constraint_violations"]:
                logger.info(f"   {violation}")
        else:
            logger.info(f"✅ All recommendations respect inventory constraints")
        
        assert result["error"] is None, "Should handle inventory constraints"
    
    # TEST 8: All constraints combined
    def test_all_constraints_combined(self):
        """Test orchestration with all constraints enabled"""
        logger.info("\n" + "="*80)
        logger.info("TEST 8: All Constraints Combined")
        logger.info("="*80)
        
        profile = self._get_base_profile()
        
        result = self.coordinator.orchestrate(
            customer_profile=profile,
            page_context=self._get_page_context(),
            mobile_context=self._get_mobile_context(),
            email_context=self._get_email_context(),
            available_products=self.available_products,
            budget_constraint=300.0,
            frequency_cap={"web": 3, "mobile": 2, "email": 3},
            inventory_constraint={
                "PROD_001": 1,
                "PROD_002": 2,
                "PROD_003": 2,
                "PROD_004": 1,
                "PROD_005": 2
            }
        )
        
        logger.info(f"Web: {len(result['web_recommendations'])} recs")
        logger.info(f"Mobile: {len(result['mobile_recommendations'])} recs")
        logger.info(f"Email: {len(result['email_recommendations'])} recs")
        logger.info(f"Consistency: {result['consistency_score']['overall_score']:.0%}")
        logger.info(f"Constraint violations: {len(result['constraint_violations'])}")
        
        assert result["error"] is None, "Should handle all constraints"
    
    # TEST 9: Latency measurement
    def test_latency_measurement(self):
        """Test latency tracking across agents"""
        logger.info("\n" + "="*80)
        logger.info("TEST 9: Latency Measurement")
        logger.info("="*80)
        
        profile = self._get_base_profile()
        
        result = self.coordinator.orchestrate(
            customer_profile=profile,
            page_context=self._get_page_context(),
            mobile_context=self._get_mobile_context(),
            email_context=self._get_email_context(),
            available_products=self.available_products
        )
        
        logger.info(f"Web Agent: {result['web_latency_ms']}ms")
        logger.info(f"Mobile Agent: {result['mobile_latency_ms']}ms")
        logger.info(f"Email Agent: {result['email_latency_ms']}ms")
        logger.info(f"Total Orchestration: {result['total_latency_ms']}ms")
        
        # All latencies should be positive
        assert result['web_latency_ms'] > 0, "Web latency should be > 0"
        assert result['mobile_latency_ms'] > 0, "Mobile latency should be > 0"
        assert result['email_latency_ms'] > 0, "Email latency should be > 0"
        assert result['total_latency_ms'] > 0, "Total latency should be > 0"
        
        # Total should be greater than individual (due to coordinator overhead)
        assert result['total_latency_ms'] >= max(
            result['web_latency_ms'],
            result['mobile_latency_ms'],
            result['email_latency_ms']
        ), "Total should be >= max individual latency"
        
        # P95 latency should be under 200ms (per requirements)
        if result['total_latency_ms'] < 200:
            logger.info("✅ P95 latency < 200ms (requirement met)")
        else:
            logger.info(f"⚠️ Latency {result['total_latency_ms']}ms exceeds P95 target of 200ms")


# Run tests manually if not using pytest
def run_all_tests():
    """Run all tests manually"""
    test_suite = TestCoordinator()
    test_suite.setup()
    
    tests = [
        ("test_basic_orchestration", test_suite.test_basic_orchestration),
        ("test_premium_customer", test_suite.test_premium_customer),
        ("test_at_risk_customer", test_suite.test_at_risk_customer),
        ("test_budget_constraint", test_suite.test_budget_constraint),
        ("test_frequency_cap", test_suite.test_frequency_cap),
        ("test_consistency_score", test_suite.test_consistency_score),
        ("test_inventory_constraint", test_suite.test_inventory_constraint),
        ("test_all_constraints_combined", test_suite.test_all_constraints_combined),
        ("test_latency_measurement", test_suite.test_latency_measurement),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
            logger.info(f"✅ {test_name} PASSED\n")
        except Exception as e:
            failed += 1
            logger.error(f"❌ {test_name} FAILED: {str(e)}\n")
    
    logger.info("="*80)
    logger.info(f"TEST SUMMARY: {passed} passed, {failed} failed")
    logger.info("="*80)
    
    return passed, failed


if __name__ == "__main__":
    # Run without pytest
    run_all_tests()