# Deploy to Azure

This repository contains Azure infrastructure templates for deploying AI Foundry services.

## Prerequisites

- Azure CLI installed and logged in
- Appropriate Azure subscription permissions

## Configuration

**First, generate a random 4-character suffix:**

```powershell
$chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
$UNIQUE_SUFFIX = -join ((1..4) | ForEach { $chars[(Get-Random -Maximum $chars.Length)] })
Write-Host "Your unique suffix: $UNIQUE_SUFFIX"
```

### Required Parameters

The following parameters are passed directly on the command line:

- **uniqueSuffix**: Unique 4-character identifier (use the generated `$UNIQUE_SUFFIX` variable)

## Deployment Steps

### 1. Create Resource Group

```powershell
az group create --name "rg-contoso-agent-wks-$UNIQUE_SUFFIX" --location "West US"
```

### 2. Deploy Infrastructure

```powershell
az deployment group create `
  --resource-group "rg-contoso-agent-wks-$UNIQUE_SUFFIX" `
  --template-file skillable.bicep `
  --parameters uniqueSuffix="$UNIQUE_SUFFIX"
```

## Infrastructure Components

The `skillable.bicep` template deploys:

- **AI Foundry Hub & Project**: For AI/ML workloads
- **Model Deployments**: GPT-4o-mini

## Post-Deployment

1. **AI Services**: Access the AI Foundry hub through the Azure portal

## Troubleshooting

### AI Model Quota Issues

If you encounter quota limit errors during deployment, you may need to clean up existing model deployments:

```powershell
# List all Cognitive Services accounts (including soft-deleted ones)
az cognitiveservices account list --query "[].{Name:name, Location:location, ResourceGroup:resourceGroup, Kind:kind}"

# List model deployments in a specific Cognitive Services account
az cognitiveservices account deployment list --name <cognitive-services-account-name> --resource-group <resource-group-name>

# Delete a specific model deployment
az cognitiveservices account deployment delete --name <deployment-name> --resource-group <resource-group-name> --account-name <cognitive-services-account-name>

# Check current quota usage
az cognitiveservices usage list --location <location> --subscription <subscription-id>
```

### Purging Soft-Deleted AI Models and Accounts

AI models and Cognitive Services accounts are soft-deleted and count against quota even after deletion:

```powershell
# List account names and locations of soft-deleted accounts
az cognitiveservices account list-deleted --output json | jq -r '.[] | "\(.name)\t\(.location)\t\(.id | split("/")[8])"' | column -t -s $'\t' -N "Name,Location,ResourceGroup"

# Purge a soft-deleted Cognitive Services account (permanently removes it)
az cognitiveservices account purge `
  --location "westus" `
  --resource-group "rg-contoso-agent-wks-$UNIQUE_SUFFIX" `
  --name <cognitive-services-account-name>

# Alternative: Use REST API to purge soft-deleted account
az rest --method delete `
  --url "https://management.azure.com/subscriptions/<subscription-id>/providers/Microsoft.CognitiveServices/locations/<location>/resourceGroups/<resource-group>/deletedAccounts/<account-name>?api-version=2021-04-30"
```

**Important Notes:**

- Soft-deleted resources still count against your quota limits
- Purging permanently deletes the resource and cannot be undone
- You may need to wait 48-72 hours after purging before quota is fully released
- If you're still hitting quota limits, consider requesting a quota increase through the Azure portal

### Purging Existing Cognitive Services Resources

If you encounter quota limits or need to clean up soft-deleted Cognitive Services resources, you can purge them using:

```powershell
# List deleted Cognitive Services accounts
az cognitiveservices account list-deleted --query "[].{Name:name, Location:location}" --output table

# Purge a specific deleted account (replace with your subscription ID, location, and resource name)
az cognitiveservices account purge `
  --location "westus" `
  --resource-group "rg-contoso-agent-wks-$UNIQUE_SUFFIX" `
  --name your-cognitiveservices-account-name

**Note**: Purging permanently deletes the resource and cannot be undone. This is typically needed when redeploying with the same resource names or when hitting subscription quotas.

## Cleanup

### Delete All Resources (Recommended)

To remove all deployed resources at once:

```powershell
# Delete the entire resource group (removes all contained resources)
az group delete --name "rg-contoso-agent-wks-$UNIQUE_SUFFIX" --yes --no-wait
```

### Delete Individual Resources (If Needed)

If you need to delete specific resources while keeping others:

```powershell
# Delete AI Foundry resources
az cognitiveservices account delete --name <ai-services-name> --resource-group "rg-contoso-agent-wks-$UNIQUE_SUFFIX"
```

### Verify Cleanup

```powershell
# Check if resource group is empty
az resource list --resource-group "rg-contoso-agent-wks-$UNIQUE_SUFFIX"

# Check for any remaining Cognitive Services (soft-deleted)
az cognitiveservices account list-deleted
```

**Note**: Some Azure services (like Cognitive Services) have soft-delete protection. Use the purge commands from the Troubleshooting section if you need to permanently remove them.
