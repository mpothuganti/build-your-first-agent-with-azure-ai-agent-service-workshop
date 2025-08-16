targetScope = 'resourceGroup'

// Parameters
@description('Location of the resources')
param location string = 'westus'

@description('Friendly name for your Azure AI resource')
param aiProjectFriendlyName string = 'Contoso Agent Service Project'

@description('Description of your Azure AI resource displayed in Azure AI Foundry')
param aiProjectDescription string = 'Project resources required for the Contoso Agent Workshop.'

@description('Set of tags to apply to all resources.')
param tags object = {}

@description('Array of models to deploy')
param models array = [
  {
    name: 'gpt-4o-mini'
    format: 'OpenAI'
    version: '2024-07-18'
    skuName: 'GlobalStandard'
    capacity: 140
  }
]

@description('Unique suffix for the resources. Must be 6 characters long.')
@maxLength(6)
@minLength(6)
param uniqueSuffix string

// Variables
var defaultTags = {
  source: 'Azure AI Foundry Agents Service lab'
}

var rootTags = union(defaultTags, tags)

// Calculate resource names
var aiProjectName = toLower('prj-contoso-agent-${uniqueSuffix}')
var foundryResourceName = toLower('fdy-contoso-agent-${uniqueSuffix}')

// Azure AI Foundry Account
resource foundryAccount 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
  name: foundryResourceName
  location: location
  sku: {
    name: 'S0'
  }
  kind: 'AIServices'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    apiProperties: {}
    allowProjectManagement: true
    customSubDomainName: foundryResourceName
    networkAcls: {
      defaultAction: 'Allow'
      virtualNetworkRules: []
      ipRules: []
    }
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: true
    defaultProject: aiProjectName
    associatedProjects: [aiProjectName]
  }
  tags: rootTags
}

// Azure AI Foundry Project
resource foundryProject 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  parent: foundryAccount
  name: aiProjectName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    description: aiProjectDescription
    displayName: aiProjectFriendlyName
  }
  tags: rootTags
}

// Model Deployments - Deploy one at a time to avoid conflicts
@batchSize(1)
resource modelDeployments 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = [for (model, index) in models: {
  parent: foundryAccount
  name: model.name
  sku: {
    capacity: model.capacity
    name: model.skuName
  }
  properties: {
    model: {
      name: model.name
      format: model.format
      version: model.version
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
    currentCapacity: model.capacity
  }
  tags: rootTags
  dependsOn: [
    foundryProject
  ]
}]

// Outputs
output resourceGroupName string = resourceGroup().name
output aiFoundryName string = foundryAccount.name
output aiProjectName string = foundryProject.name
output projectsEndpoint string = '${foundryAccount.properties.endpoints['AI Foundry API']}api/projects/${foundryProject.name}'
output deployedModels array = [for (model, index) in models: {
  name: model.name
  deploymentName: modelDeployments[index].name
}]
