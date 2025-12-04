
import os
from google.cloud import aiplatform

import os
import google.auth
from google.cloud import aiplatform

def list_locations():
    print("--- Vertex AI Location Diagnostic ---")
    
    try:
        credentials, project = google.auth.default()
        print(f"✅ Authenticated as: {credentials.service_account_email}")
        print(f"✅ Project ID: {project}")
        
        aiplatform.init(project=project, credentials=credentials)
        
        # List locations
        print("\nListing available locations...")
        # Note: aiplatform.Location is not directly exposed in some versions, 
        # but we can try to initialize and see if it works, or use a simple list call if available.
        # Actually, let's just try to list jobs or something simple in us-central1 to check connectivity.
        
        # Better: Try to get a specific location
        loc = aiplatform.gapic.JobServiceClient(credentials=credentials)
        # This is getting complicated. Let's stick to a simple model list in a loop over common regions.
        
        common_regions = ["us-central1", "asia-northeast3", "asia-northeast1", "europe-west1"]
        
        for region in common_regions:
            print(f"\nChecking region: {region}")
            try:
                aiplatform.init(project=project, location=region)
                # Try to list ANY model (custom) just to check API access
                models = aiplatform.Model.list()
                print(f"✅ Region {region} is accessible (Found {len(models)} custom models)")
            except Exception as e:
                print(f"❌ Region {region} access failed: {e}")

    except Exception as e:
        print(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    list_locations()
