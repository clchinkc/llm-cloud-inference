#!/bin/bash
# Security setup helper for LLM Cloud Inference
#
# Note: The GitHub Actions deployment workflow automatically handles:
#   - Disabling unauthenticated access
#   - Creating the llm-client service account
#   - Granting llm-client access
#
# This script is useful for:
#   - Manual deployments (outside GitHub Actions)
#   - Granting access to additional users or service accounts
#   - Key rotation and management
#   - Testing and troubleshooting authentication
#
# Usage: ./scripts/security_setup.sh [command] [args]

set -e

# Get project ID
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "Error: GCP project not set. Run: gcloud config set project YOUR_PROJECT"
    exit 1
fi

SERVICE_NAME="llm-api"
REGION="${GCP_REGION:-asia-southeast1}"  # asia-southeast1 supports nvidia-l4 GPU

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_blue() {
    echo -e "${BLUE}$1${NC}"
}

echo_green() {
    echo -e "${GREEN}✓ $1${NC}"
}

echo_yellow() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Command: enable-auth
enable_auth() {
    echo_blue "Enabling authentication for $SERVICE_NAME..."
    gcloud run services update $SERVICE_NAME \
        --no-allow-unauthenticated \
        --region $REGION
    echo_green "Authentication enabled"
}

# Command: disable-auth
disable_auth() {
    echo_yellow "Disabling authentication for $SERVICE_NAME..."
    echo "This will make the API publicly accessible without authentication."
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gcloud run services update $SERVICE_NAME \
            --allow-unauthenticated \
            --region $REGION
        echo_green "Authentication disabled (public access enabled)"
    else
        echo "Cancelled"
    fi
}

# Command: grant-user
grant_user() {
    if [ -z "$1" ]; then
        echo "Usage: $0 grant-user <email>"
        exit 1
    fi

    USER_EMAIL=$1
    echo_blue "Granting access to $USER_EMAIL..."

    gcloud run services add-iam-policy-binding $SERVICE_NAME \
        --member=user:$USER_EMAIL \
        --role=roles/run.invoker \
        --region $REGION

    echo_green "Access granted to $USER_EMAIL"
}

# Command: revoke-user
revoke_user() {
    if [ -z "$1" ]; then
        echo "Usage: $0 revoke-user <email>"
        exit 1
    fi

    USER_EMAIL=$1
    echo_blue "Revoking access from $USER_EMAIL..."

    gcloud run services remove-iam-policy-binding $SERVICE_NAME \
        --member=user:$USER_EMAIL \
        --role=roles/run.invoker \
        --region $REGION \
        --quiet

    echo_green "Access revoked from $USER_EMAIL"
}

# Command: create-service-account
create_service_account() {
    SA_NAME=${1:-llm-client}
    echo_blue "Creating service account: $SA_NAME..."

    # Check if already exists
    if gcloud iam service-accounts describe $SA_NAME@${PROJECT_ID}.iam.gserviceaccount.com &>/dev/null; then
        echo_yellow "Service account already exists"
        return
    fi

    gcloud iam service-accounts create $SA_NAME \
        --display-name="LLM API Client"

    echo_green "Service account created: $SA_NAME@${PROJECT_ID}.iam.gserviceaccount.com"
}

# Command: grant-service-account
grant_service_account() {
    SA_NAME=${1:-llm-client}
    SA_EMAIL="$SA_NAME@${PROJECT_ID}.iam.gserviceaccount.com"

    echo_blue "Granting access to service account: $SA_EMAIL..."

    gcloud run services add-iam-policy-binding $SERVICE_NAME \
        --member=serviceAccount:$SA_EMAIL \
        --role=roles/run.invoker \
        --region $REGION

    echo_green "Access granted to $SA_EMAIL"
}

# Command: create-key
create_key() {
    SA_NAME=${1:-llm-client}
    KEY_FILE="llm-client-key.json"

    if [ -f "$KEY_FILE" ]; then
        echo_yellow "Key file $KEY_FILE already exists"
        read -p "Overwrite? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Cancelled"
            return
        fi
    fi

    echo_blue "Creating key for service account: $SA_NAME..."

    gcloud iam service-accounts keys create $KEY_FILE \
        --iam-account=$SA_NAME@${PROJECT_ID}.iam.gserviceaccount.com

    echo_green "Key created: $KEY_FILE"
    echo_yellow "Keep this file secure! Add to .gitignore:"
    echo "  echo '$KEY_FILE' >> .gitignore"
}

# Command: list-access
list_access() {
    echo_blue "Current IAM bindings for $SERVICE_NAME:"
    gcloud run services get-iam-policy $SERVICE_NAME \
        --region $REGION \
        --format='value(bindings[].members[])'
}

# Command: test-auth
test_auth() {
    echo_blue "Testing authentication..."

    TOKEN=$(gcloud auth print-identity-token)
    URL=$(gcloud run services describe $SERVICE_NAME \
        --region $REGION \
        --format 'value(status.url)')

    echo "Testing: $URL/v1/models"

    RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
        "$URL/v1/models" -w "\n%{http_code}")

    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    if [ "$HTTP_CODE" = "200" ]; then
        echo_green "Authentication successful (HTTP 200)"
        echo "$BODY" | jq . || echo "$BODY"
    else
        echo -e "${YELLOW}HTTP $HTTP_CODE${NC}"
        echo "Response: $BODY"
    fi
}

# Command: view-logs
view_logs() {
    LIMIT=${1:-50}
    echo_blue "Viewing last $LIMIT logs..."
    gcloud run services logs read $SERVICE_NAME \
        --region $REGION \
        --limit $LIMIT
}

# Command: rotate-keys
rotate_keys() {
    SA_NAME=${1:-llm-client}
    SA_EMAIL="$SA_NAME@${PROJECT_ID}.iam.gserviceaccount.com"

    echo_blue "Rotating keys for $SA_EMAIL..."

    # List current keys
    echo "Current keys:"
    gcloud iam service-accounts keys list \
        --iam-account=$SA_EMAIL \
        --format='table(name,created,validAfterTime)' \
        --filter="keyType=USER_MANAGED"

    # Create new key
    NEW_KEY="llm-client-key-$(date +%Y%m%d).json"
    echo_blue "Creating new key: $NEW_KEY"
    gcloud iam service-accounts keys create $NEW_KEY \
        --iam-account=$SA_EMAIL

    echo_green "New key created: $NEW_KEY"
    echo_yellow "Update your applications to use the new key, then delete the old one"
}

# Command: quick-setup
quick_setup() {
    echo_blue "Quick security setup..."

    echo "1. Creating service account..."
    create_service_account llm-client

    echo "2. Granting service account access..."
    grant_service_account llm-client

    echo "3. Creating key file..."
    create_key llm-client

    echo "4. Enabling authentication..."
    enable_auth

    echo ""
    echo_green "Security setup complete!"
    echo ""
    echo "Next steps:"
    echo "1. Keep llm-client-key.json secure (add to .gitignore)"
    echo "2. Grant access to users: $0 grant-user user@example.com"
    echo "3. Test authentication: $0 test-auth"
    echo "4. View access logs: $0 view-logs"
}

# Show help
show_help() {
    cat << EOF
LLM Cloud Inference Security Management

Usage: $0 [command] [args]

Commands:
  grant-user <email>       Grant access to a user (most common)
  revoke-user <email>      Revoke user access
  list-access              List all users with access
  test-auth                Test authentication with your credentials

  create-service-account   Create a service account for apps
  grant-service-account    Grant service account access
  create-key              Create service account key file
  rotate-keys             Rotate service account keys

  enable-auth              Disable unauthenticated access (GitHub Actions handles this automatically)
  disable-auth             Enable unauthenticated access

  view-logs [limit]        View service logs (default: 50 lines)
  quick-setup              Complete manual setup (GitHub Actions handles this automatically)
  help                     Show this help message

Examples:
  # Grant access to a user (most common operation)
  $0 grant-user alice@example.com
  $0 revoke-user bob@example.com
  $0 list-access

  # Test your authentication works
  $0 test-auth

  # Create and grant service account (for applications)
  $0 create-service-account my-app
  $0 grant-service-account my-app
  $0 create-key my-app

  # Rotate keys for existing service account
  $0 rotate-keys llm-client

  # View logs
  $0 view-logs 100

Note: GitHub Actions deployment workflow automatically:
  - Disables unauthenticated access
  - Creates the llm-client service account
  - Grants llm-client access

For detailed documentation, see: docs/SECURITY.md
EOF
}

# Main
case "${1:-help}" in
    enable-auth)
        enable_auth
        ;;
    disable-auth)
        disable_auth
        ;;
    grant-user)
        grant_user "$2"
        ;;
    revoke-user)
        revoke_user "$2"
        ;;
    create-service-account)
        create_service_account "${2:-llm-client}"
        ;;
    grant-service-account)
        grant_service_account "${2:-llm-client}"
        ;;
    create-key)
        create_key "${2:-llm-client}"
        ;;
    rotate-keys)
        rotate_keys "${2:-llm-client}"
        ;;
    list-access)
        list_access
        ;;
    test-auth)
        test_auth
        ;;
    view-logs)
        view_logs "${2:-50}"
        ;;
    quick-setup)
        quick_setup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
