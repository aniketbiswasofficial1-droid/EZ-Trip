"""
Test script to check if Photon API is accessible
Run this to debug the location search issue
"""

import httpx
import asyncio

async def test_photon_api():
    print("Testing Photon API access...\n")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            print("1. Attempting to connect to Photon API...")
            print("   URL: https://photon.komoot.io/api/?q=Paris&limit=10")
            
            response = await client.get(
                "https://photon.komoot.io/api/",
                params={"q": "Paris", "limit": 10}
            )
            
            print(f"2. Response status code: {response.status_code}\n")
            
            if response.status_code == 200:
                data = response.json()
                features = data.get("features", [])
                print(f"✅ SUCCESS! Photon API is working")
                print(f"   Found {len(features)} results for 'Paris'\n")
                
                if features:
                    first = features[0]
                    props = first.get("properties", {})
                    print("   First result:")
                    print(f"   - Name: {props.get('name')}")
                    print(f"   - Country: {props.get('country')}")
                    print(f"   - State: {props.get('state')}")
                    
                return True
            else:
                print(f"❌ ERROR: Unexpected status code: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
                
    except httpx.ConnectError as e:
        print(f"❌ CONNECTION ERROR")
        print(f"   Cannot connect to Photon API")
        print(f"   Error: {e}")
        print(f"\n   Possible causes:")
        print(f"   - No internet connection")
        print(f"   - Firewall blocking outbound HTTPS")
        print(f"   - Photon API is down")
        return False
        
    except httpx.TimeoutException as e:
        print(f"❌ TIMEOUT ERROR")
        print(f"   Request timed out after 10 seconds")
        print(f"   Error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR")
        print(f"   Error: {e}")
        print(f"   Type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Photon API Connectivity Test")
    print("=" * 60 + "\n")
    
    result = asyncio.run(test_photon_api())
    
    print("\n" + "=" * 60)
    if result:
        print("✅ Photon API is accessible from your machine")
        print("   The issue might be in the backend configuration")
    else:
        print("❌ Cannot reach Photon API")
        print("   This is likely a network/connectivity issue")
    print("=" * 60)
