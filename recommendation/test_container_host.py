"""
Test script for containerized recommendation service
This script tests the container-host API communication
"""
import asyncio
import json
import logging
import time
from typing import Dict, Any

import aiohttp
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContainerHostTest:
    def __init__(self):
        self.host_api_url = "http://localhost:8000"  # Backend API on host
        self.container_api_url = "http://localhost:8001"  # Recommendation service in container
    
    def test_host_api_availability(self) -> bool:
        """Test if the host backend API is running"""
        logger.info("🧪 Testing host backend API availability...")
        
        try:
            response = requests.get(f"{self.host_api_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Host backend API is running and healthy")
                return True
            else:
                logger.error(f"❌ Host backend API returned status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Cannot reach host backend API: {e}")
            return False
    
    def test_container_api_availability(self) -> bool:
        """Test if the containerized recommendation service is running"""
        logger.info("🐳 Testing containerized recommendation service availability...")
        
        try:
            response = requests.get(f"{self.container_api_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Container recommendation service is running and healthy")
                data = response.json()
                logger.info(f"Backend API configured at: {data.get('backend_api', 'Unknown')}")
                return True
            else:
                logger.error(f"❌ Container recommendation service returned status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Cannot reach container recommendation service: {e}")
            return False
    
    def test_host_api_endpoints(self) -> bool:
        """Test key host backend API endpoints"""
        logger.info("🔍 Testing host backend API endpoints...")
        
        endpoints_to_test = [
            ("/users", "Users endpoint"),
            ("/dishes", "Dishes endpoint"),
            ("/restaurants", "Restaurants endpoint")
        ]
        
        success = True
        for endpoint, name in endpoints_to_test:
            try:
                response = requests.get(f"{self.host_api_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    count = len(data) if isinstance(data, list) else "unknown"
                    logger.info(f"✅ {name}: {count} items")
                else:
                    logger.error(f"❌ {name} failed with status {response.status_code}")
                    success = False
            except Exception as e:
                logger.error(f"❌ {name} error: {e}")
                success = False
        
        return success
    
    def test_container_host_communication(self) -> bool:
        """Test if container can get recommendations (which requires host API access)"""
        logger.info("🔗 Testing container-host communication via recommendations...")
        
        # Test user IDs that should exist in mock data
        test_users = [1, 2, 3]
        success = True
        
        for user_id in test_users:
            try:
                logger.info(f"Testing recommendations for user {user_id}...")
                response = requests.get(
                    f"{self.container_api_url}/api/v1/recommendations/{user_id}",
                    params={"limit": 3},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    recommendations = data.get("recommendations", [])
                    
                    if recommendations:
                        logger.info(f"✅ User {user_id}: Got {len(recommendations)} recommendations")
                        
                        # Show first recommendation details
                        first_rec = recommendations[0]
                        dish_name = first_rec.get("dish", {}).get("name", "Unknown")
                        confidence = first_rec.get("confidence_score", 0)
                        logger.info(f"   Top recommendation: {dish_name} (confidence: {confidence:.2f})")
                    else:
                        logger.warning(f"⚠️ User {user_id}: No recommendations returned")
                else:
                    logger.error(f"❌ User {user_id}: API returned status {response.status_code}")
                    if response.content:
                        logger.error(f"Response: {response.text}")
                    success = False
                    
            except Exception as e:
                logger.error(f"❌ User {user_id} recommendation test failed: {e}")
                success = False
        
        return success
    
    def run_full_test(self) -> bool:
        """Run complete test suite"""
        logger.info("🚀 Starting container-host communication test suite")
        logger.info("=" * 60)
        
        # Test 1: Host API availability
        host_api_ok = self.test_host_api_availability()
        if not host_api_ok:
            logger.error("❌ Host API test failed - aborting remaining tests")
            return False
        
        # Test 2: Container API availability
        container_api_ok = self.test_container_api_availability()
        if not container_api_ok:
            logger.error("❌ Container API test failed - aborting remaining tests")
            return False
        
        # Test 3: Host API endpoints
        endpoints_ok = self.test_host_api_endpoints()
        if not endpoints_ok:
            logger.warning("⚠️ Some host API endpoints failed - continuing anyway")
        
        # Test 4: Container-host communication
        communication_ok = self.test_container_host_communication()
        
        # Summary
        logger.info("=" * 60)
        if host_api_ok and container_api_ok and communication_ok:
            logger.info("🎉 All tests passed! Container-host communication is working correctly.")
            return True
        else:
            logger.error("❌ Some tests failed. Check the logs above for details.")
            return False

def main():
    """Main test function"""
    print("Container-Host Communication Test")
    print("================================")
    print()
    print("This test verifies that:")
    print("1. The host backend API (mock database) is running on localhost:8000")
    print("2. The containerized recommendation service is running on localhost:8001")
    print("3. The container can successfully call the host API to get recommendations")
    print()
    
    # Wait a moment for services to be ready
    logger.info("⏳ Waiting 5 seconds for services to be ready...")
    time.sleep(5)
    
    # Run tests
    tester = ContainerHostTest()
    success = tester.run_full_test()
    
    if success:
        print()
        print("✅ SUCCESS: Container-host setup is working correctly!")
        print("You can now use the containerized recommendation service.")
        return 0
    else:
        print()
        print("❌ FAILED: There are issues with the setup.")
        print("Please check the logs above and ensure:")
        print("- Host backend API is running: python mock_database/api.py")
        print("- Container is running: docker-compose -f docker-compose.simple.yml up")
        return 1

if __name__ == "__main__":
    exit(main())