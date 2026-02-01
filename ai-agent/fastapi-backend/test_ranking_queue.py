"""
Quick Test Script for Ranking Agent & Queue System
Run this after starting the FastAPI server to test the new endpoints.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

# Replace with your actual JWT token after logging in
JWT_TOKEN = "your-jwt-token-here"

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}

def test_rank_jobs():
    """Test job ranking endpoint"""
    print("\n=== Testing Job Ranking ===")
    
    payload = {
        "user_email": "test@example.com",
        "max_results": 10
    }
    
    response = requests.post(
        f"{BASE_URL}/api/jobs/rank",
        headers=headers,
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total jobs ranked: {data['total_jobs']}")
        print(f"Top 3 matches:")
        for i, job in enumerate(data['ranked_jobs'][:3], 1):
            print(f"  {i}. {job['title']} at {job['company']} - Score: {job['match_score']}")
    else:
        print(f"Error: {response.text}")


def test_add_to_queue(job_id, match_score):
    """Test adding a job to queue"""
    print(f"\n=== Adding Job {job_id} to Queue ===")
    
    response = requests.post(
        f"{BASE_URL}/api/jobs/queue/add",
        headers=headers,
        params={"job_id": job_id, "match_score": match_score}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    return response.json().get("queue_item_id")


def test_batch_add_to_queue(jobs):
    """Test batch adding jobs to queue"""
    print(f"\n=== Batch Adding {len(jobs)} Jobs to Queue ===")
    
    payload = {"jobs": jobs}
    
    response = requests.post(
        f"{BASE_URL}/api/jobs/queue/add-batch",
        headers=headers,
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")


def test_get_queue_status():
    """Test getting queue status"""
    print("\n=== Getting Queue Status ===")
    
    response = requests.get(
        f"{BASE_URL}/api/jobs/queue/status",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total in queue: {data['total_in_queue']}")
        print(f"By status: {data['by_status']}")
        print(f"\nQueue items:")
        for item in data['jobs'][:5]:  # Show first 5
            print(f"  - {item['job_title']} at {item['company']} ({item['status']})")
    else:
        print(f"Error: {response.text}")


def test_update_queue_status(queue_item_id, new_status):
    """Test updating queue item status"""
    print(f"\n=== Updating Queue Item {queue_item_id} to {new_status} ===")
    
    response = requests.patch(
        f"{BASE_URL}/api/jobs/queue/{queue_item_id}/status",
        headers=headers,
        params={"new_status": new_status}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")


def test_remove_from_queue(queue_item_id):
    """Test removing job from queue"""
    print(f"\n=== Removing Queue Item {queue_item_id} ===")
    
    response = requests.delete(
        f"{BASE_URL}/api/jobs/queue/{queue_item_id}",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")


def run_full_test():
    """Run a complete test of all endpoints"""
    print("=" * 60)
    print("RANKING AGENT & QUEUE SYSTEM TEST SUITE")
    print("=" * 60)
    
    # Test 1: Rank jobs
    test_rank_jobs()
    
    # Test 2: Add single job to queue
    queue_item_id = test_add_to_queue(
        job_id="697f7e1b31377768af1c5b46",
        match_score=85.5
    )
    
    # Test 3: Batch add jobs
    test_batch_add_to_queue([
        {"job_id": "697f7e1b31377768af1c5b47", "match_score": 78.2},
        {"job_id": "697f7e1b31377768af1c5b48", "match_score": 92.1},
    ])
    
    # Test 4: Get queue status
    test_get_queue_status()
    
    # Test 5: Update status
    if queue_item_id:
        test_update_queue_status(queue_item_id, "SUBMITTED")
    
    # Test 6: Get queue status again
    test_get_queue_status()
    
    # Test 7: Remove from queue
    if queue_item_id:
        test_remove_from_queue(queue_item_id)
    
    # Test 8: Final queue status
    test_get_queue_status()
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    # Check if JWT token is set
    if JWT_TOKEN == "your-jwt-token-here":
        print("ERROR: Please set your JWT token in the script first!")
        print("\nTo get a token:")
        print("1. Start the server: uvicorn main:app --reload")
        print("2. Login via POST /api/auth/login")
        print("3. Copy the access_token from the response")
        print("4. Update JWT_TOKEN in this script")
    else:
        run_full_test()
