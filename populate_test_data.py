"""
Test data population script for moderation history database.

This script sends sample moderation requests to the API to populate
the database with test data for analytics verification.

Usage:
    python populate_test_data.py
"""

import requests
import time
import sys

API_URL = "http://127.0.0.1:8000/moderate"

# Test texts with varied toxicity levels
test_texts = [
    # Safe content (ALLOW)
    ("This is a great post, thanks for sharing!", "SAFE"),
    ("I really appreciate your thoughtful analysis.", "SAFE"),
    ("Interesting perspective, I learned something new.", "SAFE"),
    ("Great work on this project!", "SAFE"),
    ("Thank you for the detailed explanation.", "SAFE"),
    
    # Mild toxicity (WARNING)
    ("I disagree with your opinion, it's not very smart.", "MILD"),
    ("This is a bit silly and doesn't make sense.", "MILD"),
    ("Your argument is weak and unconvincing.", "MILD"),
    
    # Moderate toxicity (HIDE)
    ("This is stupid and you should know better.", "MODERATE"),
    ("You're being ridiculous and annoying.", "MODERATE"),
    ("What a dumb idea, seriously.", "MODERATE"),
    
    # High toxicity (BLOCK)
    ("You are an idiot and should be ashamed!", "HIGH"),
    ("This is the dumbest thing I've ever read.", "HIGH"),
    ("You're a complete moron.", "HIGH"),
    ("Shut up, you stupid fool!", "HIGH"),
    
    # Threats (BLOCK/CRITICAL)
    ("I will hurt you if you don't stop!", "THREAT"),
    ("You better watch your back.", "THREAT"),
    ("I know where you live.", "THREAT"),
]

def main():
    """Send test moderation requests to populate database."""
    print("=" * 70)
    print("MODERATION HISTORY - TEST DATA POPULATION")
    print("=" * 70)
    print(f"\nSending {len(test_texts)} moderation requests to {API_URL}...")
    print()
    
    # Check if API is running
    try:
        health_response = requests.get("http://127.0.0.1:8000/health", timeout=2)
        if health_response.status_code != 200:
            print("❌ API is not healthy. Please start the API first:")
            print("   uvicorn api.main:app --reload")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Please start the API first:")
        print("   uvicorn api.main:app --reload")
        sys.exit(1)
    
    print("✓ API is running\n")
    
    # Send moderation requests
    results = []
    for i, (text, category) in enumerate(test_texts, 1):
        try:
            response = requests.post(API_URL, json={"text": text}, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                results.append(result)
                
                # Format output
                text_display = text[:50] + "..." if len(text) > 50 else text
                action = result['action']
                severity = result['severity']
                confidence = result['confidence']
                
                # Color code based on action
                action_symbol = {
                    'ALLOW': '✅',
                    'WARNING': '⚠️',
                    'HIDE': '🙈',
                    'BLOCK': '🚫'
                }.get(action, '❓')
                
                print(f"{i:2}. [{category:8}] {action_symbol} {action:8} ({severity:8}) | {text_display}")
            else:
                print(f"{i:2}. ❌ ERROR: {response.status_code} - {response.text}")
        
        except Exception as e:
            print(f"{i:2}. ❌ EXCEPTION: {e}")
        
        # Small delay to ensure different timestamps
        time.sleep(0.1)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if results:
        action_counts = {}
        severity_counts = {}
        toxic_count = 0
        
        for result in results:
            action = result['action']
            severity = result['severity']
            
            action_counts[action] = action_counts.get(action, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            if result['is_toxic']:
                toxic_count += 1
        
        print(f"\nTotal requests: {len(results)}")
        print(f"Toxic content: {toxic_count} ({toxic_count/len(results)*100:.1f}%)")
        print(f"Safe content: {len(results) - toxic_count} ({(len(results)-toxic_count)/len(results)*100:.1f}%)")
        
        print("\nAction Distribution:")
        for action, count in sorted(action_counts.items()):
            print(f"  {action:10}: {count:2} ({count/len(results)*100:.1f}%)")
        
        print("\nSeverity Distribution:")
        for severity, count in sorted(severity_counts.items()):
            print(f"  {severity:10}: {count:2} ({count/len(results)*100:.1f}%)")
        
        print("\n" + "=" * 70)
        print("✓ Test data population complete!")
        print("=" * 70)
        print("\nVerification steps:")
        print("1. Check database:")
        print("   sqlite3 data/moderation_history.db 'SELECT COUNT(*) FROM moderation_history;'")
        print("\n2. View recent records:")
        print("   sqlite3 data/moderation_history.db 'SELECT * FROM moderation_history ORDER BY id DESC LIMIT 5;'")
        print("\n3. Start dashboard:")
        print("   streamlit run dashboard/app.py")
        print("\n4. Navigate to Analytics Dashboard page to see real data!")
    else:
        print("\n❌ No successful requests. Check API logs for errors.")

if __name__ == "__main__":
    main()
