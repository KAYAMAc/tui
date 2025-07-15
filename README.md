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
- Press **r** to refresh the current resource view
- Press **Esc** to go back to namespace selection
- Press **q** to quit

### Keyboard Shortcuts

- **q**: Quit the application
- **Esc**: Go back to previous screen
- **r**: Refresh current view
- **1-5**: Switch between resource types (on Resources screen)
- **↑/↓**: Navigate lists
- **Enter**: Select item

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

## Features in Detail

### Multi-Context Support
The dashboard automatically detects all configured Kubernetes contexts and highlights the currently active one.

### Real-time Resource Information
- **Pods**: Shows readiness status, restart counts, and current phase
- **Services**: Displays service types, cluster/external IPs, and port configurations  
- **Deployments**: Shows replica status and availability
- **ConfigMaps/Secrets**: Shows the number of data items

### Responsive Interface
The interface adapts to your terminal size and provides smooth navigation between different views.

## License

This project is open source and available under the MIT License. 