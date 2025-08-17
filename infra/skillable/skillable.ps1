Write-Host "Deploying the Azure resources..."

# Define resource group parameters
$RG_LOCATION = "westus"
$MODEL_NAME = "gpt-4o-mini"  # Updated to match the default model in Bicep template

# Generate a unique suffix
$chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
$UNIQUE_SUFFIX = -join ((1..6) | ForEach { $chars[(Get-Random -Maximum $chars.Length)] })
Write-Host "Your unique suffix: $UNIQUE_SUFFIX"

Write-Host "Creating resource group: rg-contoso-agent-workshop-$UNIQUE_SUFFIX in $RG_LOCATION"
az group create --name "rg-contoso-agent-workshop-$UNIQUE_SUFFIX" --location "West US"

# Deploy the Azure resources and save output to JSON

az deployment group create `
  --resource-group "rg-contoso-agent-workshop-$UNIQUE_SUFFIX" `
  --template-file skillable.bicep `
  --parameters uniqueSuffix="$UNIQUE_SUFFIX" | Out-File -FilePath output.json -Encoding utf8

# Parse the JSON file using native PowerShell cmdlets
if (-not (Test-Path -Path output.json)) {
    Write-Host "Error: output.json not found."
    exit -1
}

$jsonData = Get-Content output.json -Raw | ConvertFrom-Json
$outputs = $jsonData.properties.outputs

# Extract values from the JSON object
$projectsEndpoint = $outputs.projectsEndpoint.value
$resourceGroupName = $outputs.resourceGroupName.value
$subscriptionId = $outputs.subscriptionId.value
$aiAccountName = $outputs.aiAccountName.value
$aiProjectName = $outputs.aiProjectName.value

if ([string]::IsNullOrEmpty($projectsEndpoint)) {
    Write-Host "Error: projectsEndpoint not found. Possible deployment failure."
    exit -1
}

# Set the path for the .env file
$ENV_FILE_PATH = "$env:USERPROFILE\Desktop\.env"

# Delete the file if it exists
if (Test-Path $ENV_FILE_PATH) {
    Remove-Item -Path $ENV_FILE_PATH -Force
}

# Create a new file and write to it
@"
PROJECT_ENDPOINT=$projectsEndpoint
MODEL_DEPLOYMENT_NAME=$MODEL_NAME
"@ | Set-Content -Path $ENV_FILE_PATH

# Set the C# project path
# $CSHARP_PROJECT_PATH = "$env:USERPROFILE\Desktop\AgentWorkshopCSharp"

# Write-Host "Creating directory: $CSHARP_PROJECT_PATH"
# New-Item -ItemType Directory -Path $CSHARP_PROJECT_PATH -Force

# # Set the user secrets for the C# project
# dotnet user-secrets set "ConnectionStrings:AiAgentService" "$projectsEndpoint" --project "$CSHARP_PROJECT_PATH"
# dotnet user-secrets set "Azure:ModelName" "$MODEL_NAME" --project "$CSHARP_PROJECT_PATH"

# Delete the output.json file
Remove-Item -Path output.json -Force

Write-Host "Adding Azure AI Developer user role"

# Set Variables
$subId = az account show --query id --output tsv
$objectId = az ad signed-in-user show --query id -o tsv

$roleResult = az role assignment create --role "f6c7c914-8db3-469d-8ca1-694a8f32e121" `
                        --assignee-object-id "$objectId" `
                        --scope "subscriptions/$subId/resourceGroups/$resourceGroupName" `
                        --assignee-principal-type 'User'

# Check if the command failed
if ($LASTEXITCODE -ne 0) {
    Write-Host "User role assignment failed."
    exit 1
}

Write-Host "User role assignment succeeded."
