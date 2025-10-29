#!/usr/bin/env python3
"""
Log Analysis Infrastructure Setup

Automated setup of:
1. BigQuery dataset for log storage
2. Cloud Logging sink
3. IAM permissions
4. Initial schema validation

Usage:
    python setup_log_analysis.py --project naeda-genesis
    python setup_log_analysis.py --project naeda-genesis --cleanup  # Delete all resources
"""

import argparse
import sys
from typing import Optional, Dict, Any
from google.cloud import bigquery
from google.cloud.logging_v2.services.config_service_v2 import ConfigServiceV2Client
from google.cloud.logging_v2.types import LogSink
from google.api_core import exceptions
import google.auth


def create_bigquery_dataset(
    project_id: str,
    dataset_id: str = "cloud_run_logs",
    location: str = "us-central1"
) -> bool:
    """
    Create BigQuery dataset for log storage.
    
    Args:
        project_id: GCP project ID
        dataset_id: Dataset name
        location: Dataset location
        
    Returns:
        True if created or already exists, False on error
    """
    print(f"\n📊 Creating BigQuery dataset: {dataset_id}...")
    
    client = bigquery.Client(project=project_id)
    
    # Check if dataset exists
    dataset_ref = f"{project_id}.{dataset_id}"
    try:
        client.get_dataset(dataset_ref)
        print(f"✅ Dataset already exists: {dataset_ref}")
        return True
    except exceptions.NotFound:
        pass
    
    # Create dataset
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = location
    dataset.description = "Cloud Run logs for ION API and Lumen Gateway"
    
    # Set expiration (30 days retention)
    dataset.default_table_expiration_ms = 30 * 24 * 60 * 60 * 1000  # 30 days
    
    try:
        dataset = client.create_dataset(dataset, timeout=30)
        print(f"✅ Created dataset: {dataset.project}.{dataset.dataset_id}")
        print(f"   Location: {dataset.location}")
        print(f"   Retention: 30 days")
        return True
    except Exception as e:
        print(f"❌ Failed to create dataset: {e}")
        return False


def create_log_sink(
    project_id: str,
    sink_name: str = "cloud-run-logs-sink",
    dataset_id: str = "cloud_run_logs"
) -> Optional[str]:
    """
    Create Cloud Logging sink to BigQuery.
    
    Args:
        project_id: GCP project ID
        sink_name: Sink name
        dataset_id: Target BigQuery dataset
        
    Returns:
        Service account email if successful, None on error
    """
    print(f"\n📝 Creating Cloud Logging sink: {sink_name}...")
    
    client = ConfigServiceV2Client()
    parent = f"projects/{project_id}"
    
    # Check if sink exists
    sink_path = f"{parent}/sinks/{sink_name}"
    try:
        existing_sink = client.get_sink(request={"sink_name": sink_path})
        print(f"✅ Sink already exists: {sink_name}")
        print(f"   Destination: {existing_sink.destination}")
        print(f"   Service Account: {existing_sink.writer_identity}")
        return existing_sink.writer_identity
    except exceptions.NotFound:
        pass
    
    # Log filter for Cloud Run ERROR+ logs
    filter_str = """
resource.type="cloud_run_revision"
AND (
    resource.labels.service_name="ion-api"
    OR resource.labels.service_name="lumen-gateway"
)
AND severity>=ERROR
""".strip()
    
    # Create sink
    sink = LogSink(
        name=sink_name,
        destination=f"bigquery.googleapis.com/projects/{project_id}/datasets/{dataset_id}",
        filter=filter_str,
        description="Export Cloud Run ERROR+ logs to BigQuery for analysis"
    )
    
    try:
        created_sink = client.create_sink(
            request={
                "parent": parent,
                "sink": sink
            }
        )
        print(f"✅ Created sink: {sink_name}")
        print(f"   Destination: {created_sink.destination}")
        print(f"   Service Account: {created_sink.writer_identity}")
        print(f"\n📋 Log Filter:")
        for line in filter_str.split('\n'):
            print(f"   {line}")
        
        return created_sink.writer_identity
    except Exception as e:
        print(f"❌ Failed to create sink: {e}")
        return None


def grant_bigquery_permissions(
    project_id: str,
    service_account: str,
    dataset_id: str = "cloud_run_logs"
) -> bool:
    """
    Grant BigQuery Data Editor role to sink service account.
    
    Args:
        project_id: GCP project ID
        service_account: Service account email
        dataset_id: Dataset ID
        
    Returns:
        True if successful, False on error
    """
    print(f"\n🔐 Granting BigQuery permissions to {service_account}...")
    
    client = bigquery.Client(project=project_id)
    dataset_ref = f"{project_id}.{dataset_id}"
    
    try:
        dataset = client.get_dataset(dataset_ref)
        
        # Get current ACL
        entries = list(dataset.access_entries)
        
        # Check if permission already exists
        for entry in entries:
            if entry.entity_type == "userByEmail" and entry.entity_id == service_account:
                print(f"✅ Permission already granted")
                return True
        
        # Add new permission
        new_entry = bigquery.AccessEntry(
            role="WRITER",
            entity_type="userByEmail",
            entity_id=service_account
        )
        entries.append(new_entry)
        
        dataset.access_entries = entries
        client.update_dataset(dataset, ["access_entries"])
        
        print(f"✅ Granted WRITER role to {service_account}")
        return True
    except Exception as e:
        print(f"❌ Failed to grant permissions: {e}")
        print(f"\n⚠️  Manual Grant Required:")
        print(f"   gcloud projects add-iam-policy-binding {project_id} \\")
        print(f"     --member='{service_account}' \\")
        print(f"     --role='roles/bigquery.dataEditor'")
        return False


def verify_setup(project_id: str, dataset_id: str = "cloud_run_logs") -> Dict[str, Any]:
    """
    Verify infrastructure setup.
    
    Args:
        project_id: GCP project ID
        dataset_id: Dataset ID
        
    Returns:
        Status dictionary
    """
    print(f"\n🔍 Verifying setup...")
    
    status = {
        "dataset_exists": False,
        "sink_exists": False,
        "tables_exist": False,
        "table_count": 0
    }
    
    # Check dataset
    bq_client = bigquery.Client(project=project_id)
    dataset_ref = f"{project_id}.{dataset_id}"
    try:
        dataset = bq_client.get_dataset(dataset_ref)
        status["dataset_exists"] = True
        print(f"✅ Dataset exists: {dataset_ref}")
        
        # List tables
        tables = list(bq_client.list_tables(dataset))
        status["tables_exist"] = len(tables) > 0
        status["table_count"] = len(tables)
        
        if tables:
            print(f"✅ Tables created: {len(tables)}")
            for table in tables[:5]:  # Show first 5
                print(f"   - {table.table_id}")
            if len(tables) > 5:
                print(f"   ... and {len(tables) - 5} more")
        else:
            print(f"⏳ No tables yet (logs will create tables automatically)")
    except exceptions.NotFound:
        print(f"❌ Dataset not found: {dataset_ref}")
    
    # Check sink
    logging_client = ConfigServiceV2Client()
    sink_path = f"projects/{project_id}/sinks/cloud-run-logs-sink"
    try:
        sink = logging_client.get_sink(request={"sink_name": sink_path})
        status["sink_exists"] = True
        print(f"✅ Sink exists: cloud-run-logs-sink")
        print(f"   Writer: {sink.writer_identity}")
    except exceptions.NotFound:
        print(f"❌ Sink not found: cloud-run-logs-sink")
    
    return status


def cleanup_infrastructure(project_id: str, dataset_id: str = "cloud_run_logs") -> bool:
    """
    Delete all log analysis infrastructure.
    
    Args:
        project_id: GCP project ID
        dataset_id: Dataset ID
        
    Returns:
        True if successful, False on error
    """
    print(f"\n🗑️  Cleaning up infrastructure...")
    
    success = True
    
    # Delete sink
    logging_client = ConfigServiceV2Client()
    sink_path = f"projects/{project_id}/sinks/cloud-run-logs-sink"
    try:
        logging_client.delete_sink(request={"sink_name": sink_path})
        print(f"✅ Deleted sink: cloud-run-logs-sink")
    except exceptions.NotFound:
        print(f"⚠️  Sink not found (already deleted)")
    except Exception as e:
        print(f"❌ Failed to delete sink: {e}")
        success = False
    
    # Delete dataset (with all tables)
    bq_client = bigquery.Client(project=project_id)
    dataset_ref = f"{project_id}.{dataset_id}"
    try:
        bq_client.delete_dataset(dataset_ref, delete_contents=True, not_found_ok=True)
        print(f"✅ Deleted dataset: {dataset_ref}")
    except Exception as e:
        print(f"❌ Failed to delete dataset: {e}")
        success = False
    
    return success


def main():
    parser = argparse.ArgumentParser(
        description="Setup log analysis infrastructure for ION API monitoring"
    )
    parser.add_argument(
        "--project",
        required=True,
        help="GCP project ID"
    )
    parser.add_argument(
        "--dataset",
        default="cloud_run_logs",
        help="BigQuery dataset name (default: cloud_run_logs)"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete all infrastructure instead of creating"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing setup, don't create"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 ION API Log Analysis Infrastructure Setup")
    print("=" * 60)
    print(f"Project: {args.project}")
    print(f"Dataset: {args.dataset}")
    print()
    
    # Cleanup mode
    if args.cleanup:
        confirm = input("⚠️  This will DELETE all log data. Type 'DELETE' to confirm: ")
        if confirm != "DELETE":
            print("❌ Cleanup cancelled")
            return 1
        
        success = cleanup_infrastructure(args.project, args.dataset)
        return 0 if success else 1
    
    # Verify-only mode
    if args.verify_only:
        status = verify_setup(args.project, args.dataset)
        all_good = status["dataset_exists"] and status["sink_exists"]
        return 0 if all_good else 1
    
    # Setup mode
    # Step 1: Create BigQuery dataset
    if not create_bigquery_dataset(args.project, args.dataset):
        return 1
    
    # Step 2: Create log sink
    service_account = create_log_sink(args.project, dataset_id=args.dataset)
    if not service_account:
        return 1
    
    # Step 3: Grant permissions
    if not grant_bigquery_permissions(args.project, service_account, args.dataset):
        print("\n⚠️  Setup completed with warnings. Manual permission grant may be required.")
    
    # Step 4: Verify
    print("\n" + "=" * 60)
    status = verify_setup(args.project, args.dataset)
    print("=" * 60)
    
    # Summary
    print("\n📊 Setup Summary:")
    print(f"✅ BigQuery Dataset: {args.dataset}")
    print(f"✅ Log Sink: cloud-run-logs-sink")
    print(f"✅ Service Account: {service_account}")
    print(f"\n⏳ Logs will start flowing to BigQuery within 1-2 minutes")
    print(f"📝 Tables will be auto-created as logs arrive")
    
    print(f"\n🔍 Next Steps:")
    print(f"1. Wait 5-10 minutes for logs to accumulate")
    print(f"2. Run: python analyze_error_patterns.py --project {args.project}")
    print(f"3. View logs: https://console.cloud.google.com/bigquery?project={args.project}&d={args.dataset}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
