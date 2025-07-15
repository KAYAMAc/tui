# Kubernetes Dashboard

A text-based user interface (TUI) for managing Kubernetes resources using Textual.

## Features

- 📋 **Context Selection**: Choose from available Kubernetes contexts
- 🏷️ **Namespace Selection**: Browse and select namespaces within a context
- 📊 **Resource Viewing**: View and manage different types of Kubernetes resources:
  - Pods (with status, ready state, restart count)
  - Services (with type, IPs, ports)
  - Deployments (with replica status)
  - ConfigMaps (with data count)
  - Secrets (with data count)
- 🎯 **Interactive Operations**: Click on any resource to perform operations:
  - **Pods**: Get logs, describe, delete, port forward, exec shell
  - **Services**: Describe, edit, delete
  - **Deployments**: Describe, scale, restart, rollout status, edit, delete
  - **ConfigMaps/Secrets**: Describe, view data, edit, delete

## Prerequisites

- Python 3.7+
- `kubectl` installed and configured with access to your Kubernetes clusters
- Valid Kubernetes context(s) configured

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the dashboard:

```bash
python cli.py
```

### Navigation

#### Context Selection Screen
- Use **↑/↓** arrow keys to navigate contexts
- Press **Enter** to select a context
- Press **q** to quit

#### Namespace Selection Screen  
- Use **↑/↓** arrow keys to navigate namespaces
- Press **Enter** to select a namespace
- Press **r** to refresh the namespace list
- Press **Esc** to go back to context selection
- Press **q** to quit

#### Resources Screen
- Use **buttons** or **number keys (1-5)** to switch between resource types:
  - **1**: Pods
  - **2**: Services  
  - **3**: Deployments
  - **4**: ConfigMaps
  - **5**: Secrets
- **Click on any resource row** to see available operations
- Press **r** to refresh the current resource view
- Press **Esc** to go back to namespace selection
- Press **q** to quit

#### Operations Screen
- Select an operation from the list using **↑/↓** arrow keys
- Press **Enter** to execute the selected operation
- Press **Esc** to go back to resources view
- Press **q** to quit

#### Operation Results
- View the output of operations in a modal dialog
- Press **Esc** or **q** to close the results and return to operations

### Available Operations by Resource Type

#### 📦 Pods
- **📋 Describe**: Show detailed information about the pod
- **📜 Get Logs**: Retrieve current logs from the pod
- **📜 Get Previous Logs**: Retrieve logs from the previous container instance
- **🔗 Port Forward**: Set up port forwarding (shows command to run)
- **💻 Exec Shell**: Execute a shell in the pod (shows command to run)
- **📝 Edit**: Edit the pod resource (shows command to run)
- **🗑️ Delete**: Delete the pod (shows confirmation command)

#### 🌐 Services
- **📋 Describe**: Show detailed information about the service
- **📝 Edit**: Edit the service resource (shows command to run)
- **🗑️ Delete**: Delete the service (shows confirmation command)

#### 🚀 Deployments
- **📋 Describe**: Show detailed information about the deployment
- **📏 Scale**: Scale the deployment (shows scaling commands)
- **🔄 Restart Rollout**: Restart the deployment rollout (executes immediately)
- **📊 Rollout Status**: Check the rollout status (executes immediately)
- **📝 Edit**: Edit the deployment resource (shows command to run)
- **🗑️ Delete**: Delete the deployment (shows confirmation command)

#### 📄 ConfigMaps & Secrets
- **📋 Describe**: Show detailed information about the resource
- **👁️ View Data**: View the data contents in YAML format
- **📝 Edit**: Edit the resource (shows command to run)
- **🗑️ Delete**: Delete the resource (shows confirmation command)

### Keyboard Shortcuts

- **q**: Quit the application
- **Esc**: Go back to previous screen
- **r**: Refresh current view
- **1-5**: Switch between resource types (on Resources screen)
- **↑/↓**: Navigate lists and tables
- **Enter**: Select item or execute operation
- **Click**: Select resource row (on Resources screen)

## Operation Safety

The dashboard implements different safety levels for operations:

### 🟢 Safe Operations (Execute Immediately)
- Describe resources
- Get logs
- View data
- Check rollout status
- Restart deployments

### 🟡 Interactive Operations (Show Command)
- Port forwarding
- Exec shell
- Edit resources

### 🔴 Destructive Operations (Show Warning + Command)
- Delete resources
- Scale deployments

For safety reasons, destructive operations show the kubectl command rather than executing directly, allowing you to review and run them manually.

## Requirements

- **kubectl**: The dashboard uses `kubectl` commands to interact with Kubernetes clusters
- **Kubernetes Context**: At least one configured Kubernetes context
- **Network Access**: Access to your Kubernetes cluster(s)

## Troubleshooting

### "No Kubernetes contexts found"
- Ensure `kubectl` is installed: `kubectl version --client`
- Configure at least one context: `kubectl config get-contexts`
- Test cluster access: `kubectl cluster-info`

### "Error loading namespaces/resources"
- Check your Kubernetes cluster connectivity
- Verify you have proper RBAC permissions
- Ensure the selected context is valid and accessible

### Permission Issues
- Make sure your Kubernetes user/service account has the necessary permissions:
  - `get` permission on namespaces
  - `list` and `get` permissions on pods, services, deployments, configmaps, secrets
  - Additional permissions for operations you want to perform (e.g., `delete`, `patch`, `update`)

### Operation Failures
- Verify you have the necessary RBAC permissions for the specific operation
- Check that the resource still exists (it might have been deleted by another process)
- Ensure the cluster is accessible and responsive

## Features in Detail

### Multi-Context Support
The dashboard automatically detects all configured Kubernetes contexts and highlights the currently active one.

### Real-time Resource Information
- **Pods**: Shows readiness status, restart counts, current phase, and age since creation
- **Services**: Displays service types, cluster/external IPs, port configurations, and age
- **Deployments**: Shows replica status, availability, and age since creation
- **ConfigMaps/Secrets**: Shows the number of data items and age since creation

### Interactive Operations
Click on any resource to see context-sensitive operations. The dashboard automatically adjusts available operations based on the resource type.

### Responsive Interface
The interface adapts to your terminal size and provides smooth navigation between different views with modal dialogs for operation results.

### Operation Results Display
All operation outputs are displayed in scrollable modal windows with proper formatting, making it easy to read logs, descriptions, and other information.

### Age Display Format
The dashboard shows resource age in a human-readable format similar to kubectl:
- `45s` - Created less than a minute ago
- `30m` - Created 30 minutes ago  
- `2h` - Created 2 hours ago
- `5d` - Created 5 days ago

## License

This project is open source and available under the MIT License. 