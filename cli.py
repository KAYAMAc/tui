#!/usr/bin/env python3
"""
Kubernetes Dashboard - A Textual-based TUI for managing Kubernetes resources
"""

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual.widgets import Header, Footer, Button, Static, ListView, ListItem, Label, Select, DataTable
from textual.screen import Screen, ModalScreen
from textual.binding import Binding
from textual import on
import asyncio
import subprocess
import json
from typing import List, Dict, Any, Optional


class OperationResultScreen(ModalScreen):
    """Modal screen for displaying operation results"""
    
    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
    ]
    
    def __init__(self, title: str, content: str):
        super().__init__()
        self.title = title
        self.content = content
    
    def compose(self) -> ComposeResult:
        yield Container(
            Static(self.title, classes="modal-title"),
            Static(self.content, classes="modal-content"),
            Static("\nPress Esc or q to close", classes="modal-help"),
            classes="modal-container"
        )
    
    def action_dismiss(self) -> None:
        self.dismiss()


class OperationsScreen(Screen):
    """Screen for showing available operations on a selected resource"""
    
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("q", "quit", "Quit"),
    ]
    
    def __init__(self, context: str, namespace: str, resource_type: str, resource_name: str):
        super().__init__()
        self.context = context
        self.namespace = namespace
        self.resource_type = resource_type
        self.resource_name = resource_name
        self.operations = self._get_operations_for_resource()
    
    def _get_operations_for_resource(self) -> List[Dict[str, str]]:
        """Get available operations based on resource type"""
        if self.resource_type == "pods":
            return [
                {"name": "📋 Describe", "action": "describe"},
                {"name": "📜 Get Logs", "action": "logs"},
                {"name": "📜 Get Previous Logs", "action": "logs_previous"},
                {"name": "🔗 Port Forward", "action": "port_forward"},
                {"name": "💻 Exec Shell", "action": "exec"},
                {"name": "📝 Edit", "action": "edit"},
                {"name": "🗑️ Delete", "action": "delete"},
            ]
        elif self.resource_type == "services":
            return [
                {"name": "📋 Describe", "action": "describe"},
                {"name": "📝 Edit", "action": "edit"},
                {"name": "🗑️ Delete", "action": "delete"},
            ]
        elif self.resource_type == "deployments":
            return [
                {"name": "📋 Describe", "action": "describe"},
                {"name": "📏 Scale", "action": "scale"},
                {"name": "🔄 Restart Rollout", "action": "restart"},
                {"name": "📊 Rollout Status", "action": "rollout_status"},
                {"name": "📝 Edit", "action": "edit"},
                {"name": "🗑️ Delete", "action": "delete"},
            ]
        elif self.resource_type in ["configmaps", "secrets"]:
            return [
                {"name": "📋 Describe", "action": "describe"},
                {"name": "👁️ View Data", "action": "view_data"},
                {"name": "📝 Edit", "action": "edit"},
                {"name": "🗑️ Delete", "action": "delete"},
            ]
        else:
            return [
                {"name": "📋 Describe", "action": "describe"},
                {"name": "📝 Edit", "action": "edit"},
                {"name": "🗑️ Delete", "action": "delete"},
            ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static(f"Operations for {self.resource_type[:-1]}: {self.resource_name}", classes="title"),
            Static(f"Context: {self.context} | Namespace: {self.namespace}", classes="subtitle"),
            ListView(
                *[ListItem(Label(op["name"])) for op in self.operations],
                id="operations-list"
            ),
            Static("\nPress Enter to execute operation, Esc to go back, q to quit", classes="help"),
            classes="container"
        )
        yield Footer()
    
    @on(ListView.Selected)
    async def on_operation_selected(self, event: ListView.Selected) -> None:
        operation = self.operations[event.list_view.index]
        await self.execute_operation(operation["action"])
    
    async def execute_operation(self, action: str) -> None:
        """Execute the selected operation"""
        try:
            if action == "describe":
                await self._describe_resource()
            elif action == "logs":
                await self._get_logs(previous=False)
            elif action == "logs_previous":
                await self._get_logs(previous=True)
            elif action == "port_forward":
                await self._port_forward()
            elif action == "exec":
                await self._exec_shell()
            elif action == "edit":
                await self._edit_resource()
            elif action == "delete":
                await self._delete_resource()
            elif action == "scale":
                await self._scale_deployment()
            elif action == "restart":
                await self._restart_deployment()
            elif action == "rollout_status":
                await self._rollout_status()
            elif action == "view_data":
                await self._view_data()
        except Exception as e:
            self.app.push_screen(OperationResultScreen("Error", f"Operation failed: {str(e)}"))
    
    async def _describe_resource(self) -> None:
        """Describe the resource"""
        result = await asyncio.create_subprocess_exec(
            "kubectl", "--context", self.context, "-n", self.namespace,
            "describe", self.resource_type[:-1], self.resource_name,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        
        if result.returncode == 0:
            content = stdout.decode()
        else:
            content = f"Error: {stderr.decode()}"
        
        self.app.push_screen(OperationResultScreen(f"Describe {self.resource_name}", content))
    
    async def _get_logs(self, previous: bool = False) -> None:
        """Get logs from a pod"""
        if self.resource_type != "pods":
            return
        
        cmd = ["kubectl", "--context", self.context, "-n", self.namespace, "logs"]
        if previous:
            cmd.append("--previous")
        cmd.append(self.resource_name)
        
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        
        if result.returncode == 0:
            content = stdout.decode() or "No logs available"
        else:
            content = f"Error: {stderr.decode()}"
        
        log_type = "Previous Logs" if previous else "Logs"
        self.app.push_screen(OperationResultScreen(f"{log_type} - {self.resource_name}", content))
    
    async def _port_forward(self) -> None:
        """Set up port forwarding for a pod"""
        if self.resource_type != "pods":
            return
        
        # For demo purposes, we'll show the command that would be run
        # In a real implementation, you might want to prompt for port numbers
        cmd = f"kubectl --context {self.context} -n {self.namespace} port-forward {self.resource_name} 8080:80"
        content = f"To set up port forwarding, run:\n\n{cmd}\n\nThis will forward local port 8080 to pod port 80.\nYou can modify the ports as needed."
        
        self.app.push_screen(OperationResultScreen("Port Forward Setup", content))
    
    async def _exec_shell(self) -> None:
        """Execute shell in pod"""
        if self.resource_type != "pods":
            return
        
        # For demo purposes, we'll show the command that would be run
        # In a real implementation, you might want to open a new terminal
        cmd = f"kubectl --context {self.context} -n {self.namespace} exec -it {self.resource_name} -- /bin/bash"
        content = f"To execute a shell in the pod, run:\n\n{cmd}\n\nAlternatively, try /bin/sh if bash is not available."
        
        self.app.push_screen(OperationResultScreen("Exec Shell", content))
    
    async def _edit_resource(self) -> None:
        """Edit the resource"""
        # For demo purposes, we'll show the command that would be run
        cmd = f"kubectl --context {self.context} -n {self.namespace} edit {self.resource_type[:-1]} {self.resource_name}"
        content = f"To edit this resource, run:\n\n{cmd}\n\nThis will open the resource in your default editor."
        
        self.app.push_screen(OperationResultScreen("Edit Resource", content))
    
    async def _delete_resource(self) -> None:
        """Delete the resource"""
        # Show confirmation and command
        cmd = f"kubectl --context {self.context} -n {self.namespace} delete {self.resource_type[:-1]} {self.resource_name}"
        content = f"⚠️ WARNING: This will permanently delete the resource!\n\nTo delete this resource, run:\n\n{cmd}\n\n⚠️ This action cannot be undone!"
        
        self.app.push_screen(OperationResultScreen("Delete Resource", content))
    
    async def _scale_deployment(self) -> None:
        """Scale a deployment"""
        if self.resource_type != "deployments":
            return
        
        # For demo purposes, show scaling commands
        content = f"To scale this deployment:\n\n"
        content += f"Scale to 3 replicas:\n"
        content += f"kubectl --context {self.context} -n {self.namespace} scale deployment {self.resource_name} --replicas=3\n\n"
        content += f"Scale to 0 (stop all pods):\n"
        content += f"kubectl --context {self.context} -n {self.namespace} scale deployment {self.resource_name} --replicas=0"
        
        self.app.push_screen(OperationResultScreen("Scale Deployment", content))
    
    async def _restart_deployment(self) -> None:
        """Restart a deployment"""
        if self.resource_type != "deployments":
            return
        
        result = await asyncio.create_subprocess_exec(
            "kubectl", "--context", self.context, "-n", self.namespace,
            "rollout", "restart", "deployment", self.resource_name,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        
        if result.returncode == 0:
            content = f"✅ Deployment restart initiated successfully!\n\n{stdout.decode()}"
        else:
            content = f"❌ Error restarting deployment: {stderr.decode()}"
        
        self.app.push_screen(OperationResultScreen("Restart Deployment", content))
    
    async def _rollout_status(self) -> None:
        """Check rollout status"""
        if self.resource_type != "deployments":
            return
        
        result = await asyncio.create_subprocess_exec(
            "kubectl", "--context", self.context, "-n", self.namespace,
            "rollout", "status", "deployment", self.resource_name,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        
        if result.returncode == 0:
            content = stdout.decode()
        else:
            content = f"Error: {stderr.decode()}"
        
        self.app.push_screen(OperationResultScreen("Rollout Status", content))
    
    async def _view_data(self) -> None:
        """View data from configmap or secret"""
        if self.resource_type not in ["configmaps", "secrets"]:
            return
        
        result = await asyncio.create_subprocess_exec(
            "kubectl", "--context", self.context, "-n", self.namespace,
            "get", self.resource_type[:-1], self.resource_name, "-o", "yaml",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        
        if result.returncode == 0:
            content = stdout.decode()
        else:
            content = f"Error: {stderr.decode()}"
        
        self.app.push_screen(OperationResultScreen(f"Data - {self.resource_name}", content))
    
    def action_back(self) -> None:
        self.app.pop_screen()
    
    def action_quit(self) -> None:
        self.app.exit()


class ContextSelectionScreen(Screen):
    """Screen for selecting Kubernetes context"""
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "back", "Back"),
    ]
    
    def __init__(self, contexts: List[str], current_context: str):
        super().__init__()
        self.contexts = contexts
        self.current_context = current_context
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("Select Kubernetes Context", classes="title"),
            ListView(
                *[ListItem(Label(f"{'🔹 ' if ctx == self.current_context else '  '}{ctx}")) for ctx in self.contexts],
                id="context-list"
            ),
            Static("\nPress Enter to select, q to quit", classes="help"),
            classes="container"
        )
        yield Footer()
    
    @on(ListView.Selected)
    def on_context_selected(self, event: ListView.Selected) -> None:
        selected_context = self.contexts[event.list_view.index]
        self.app.selected_context = selected_context
        self.app.push_screen(NamespaceSelectionScreen(selected_context))
    
    def action_back(self) -> None:
        self.app.pop_screen()
    
    def action_quit(self) -> None:
        self.app.exit()


class NamespaceSelectionScreen(Screen):
    """Screen for selecting Kubernetes namespace"""
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "back", "Back"),
        Binding("r", "refresh", "Refresh"),
    ]
    
    def __init__(self, context: str):
        super().__init__()
        self.context = context
        self.namespaces = []
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static(f"Select Namespace - Context: {self.context}", classes="title"),
            ListView(id="namespace-list"),
            Static("\nPress Enter to select, r to refresh, Esc to go back, q to quit", classes="help"),
            classes="container"
        )
        yield Footer()
    
    async def on_mount(self) -> None:
        await self.load_namespaces()
    
    async def load_namespaces(self) -> None:
        try:
            self.query_one("#namespace-list", ListView).clear()
            self.query_one("#namespace-list", ListView).loading = True
            
            result = await asyncio.create_subprocess_exec(
                "kubectl", "--context", self.context, "get", "namespaces", "-o", "json",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                data = json.loads(stdout.decode())
                self.namespaces = [item['metadata']['name'] for item in data['items']]
                
                namespace_list = self.query_one("#namespace-list", ListView)
                namespace_list.clear()
                for ns in sorted(self.namespaces):
                    namespace_list.append(ListItem(Label(ns)))
            else:
                self.namespaces = []
                namespace_list = self.query_one("#namespace-list", ListView)
                namespace_list.append(ListItem(Label(f"Error: {stderr.decode()}")))
                
        except Exception as e:
            self.namespaces = []
            namespace_list = self.query_one("#namespace-list", ListView)
            namespace_list.clear()
            namespace_list.append(ListItem(Label(f"Error loading namespaces: {str(e)}")))
        finally:
            self.query_one("#namespace-list", ListView).loading = False
    
    @on(ListView.Selected)
    def on_namespace_selected(self, event: ListView.Selected) -> None:
        if self.namespaces:
            selected_namespace = self.namespaces[event.list_view.index]
            self.app.push_screen(ResourcesScreen(self.context, selected_namespace))
    
    def action_back(self) -> None:
        self.app.pop_screen()
    
    def action_quit(self) -> None:
        self.app.exit()
    
    async def action_refresh(self) -> None:
        await self.load_namespaces()


class ResourcesScreen(Screen):
    """Screen for viewing Kubernetes resources"""
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "back", "Back"),
        Binding("r", "refresh", "Refresh"),
        Binding("1", "show_pods", "Pods"),
        Binding("2", "show_services", "Services"),
        Binding("3", "show_deployments", "Deployments"),
        Binding("4", "show_configmaps", "ConfigMaps"),
        Binding("5", "show_secrets", "Secrets"),
    ]
    
    def __init__(self, context: str, namespace: str):
        super().__init__()
        self.context = context
        self.namespace = namespace
        self.current_resource = "pods"
        self.resource_names = []  # Store resource names for selection
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static(f"Resources - Context: {self.context} | Namespace: {self.namespace}", classes="title"),
            Horizontal(
                Button("Pods (1)", id="btn-pods", variant="primary"),
                Button("Services (2)", id="btn-services"),
                Button("Deployments (3)", id="btn-deployments"),
                Button("ConfigMaps (4)", id="btn-configmaps"),
                Button("Secrets (5)", id="btn-secrets"),
                classes="resource-buttons"
            ),
            DataTable(id="resources-table"),
            Static("\nClick on a resource for operations, or press number keys to switch resources", classes="help"),
            Static("r to refresh, Esc to go back, q to quit", classes="help"),
            classes="container"
        )
        yield Footer()
    
    async def on_mount(self) -> None:
        await self.load_resources("pods")
    
    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection to show operations menu"""
        if self.resource_names and event.row_index < len(self.resource_names):
            selected_resource = self.resource_names[event.row_index]
            self.app.push_screen(OperationsScreen(
                self.context, 
                self.namespace, 
                self.current_resource, 
                selected_resource
            ))
    
    async def load_resources(self, resource_type: str) -> None:
        try:
            self.current_resource = resource_type
            self.resource_names = []  # Reset resource names
            table = self.query_one("#resources-table", DataTable)
            table.clear(columns=True)
            table.loading = True
            
            # Update button styles
            for btn_id in ["btn-pods", "btn-services", "btn-deployments", "btn-configmaps", "btn-secrets"]:
                btn = self.query_one(f"#{btn_id}", Button)
                if btn_id == f"btn-{resource_type}":
                    btn.variant = "primary"
                else:
                    btn.variant = "default"
            
            result = await asyncio.create_subprocess_exec(
                "kubectl", "--context", self.context, "-n", self.namespace, 
                "get", resource_type, "-o", "json",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                data = json.loads(stdout.decode())
                items = data.get('items', [])
                
                if items:
                    # Set up columns based on resource type
                    if resource_type == "pods":
                        table.add_columns("Name", "Ready", "Status", "Restarts", "Age")
                        for item in items:
                            name = item['metadata']['name']
                            self.resource_names.append(name)
                            status = item['status']['phase']
                            
                            # Calculate ready containers
                            containers = item['status'].get('containerStatuses', [])
                            ready_count = sum(1 for c in containers if c.get('ready', False))
                            total_count = len(containers)
                            ready = f"{ready_count}/{total_count}"
                            
                            # Calculate restarts
                            restarts = sum(c.get('restartCount', 0) for c in containers)
                            
                            # Calculate age
                            creation_time = item['metadata']['creationTimestamp']
                            age = "Unknown"  # Simplified for now
                            
                            table.add_row(name, ready, status, str(restarts), age)
                    
                    elif resource_type == "services":
                        table.add_columns("Name", "Type", "Cluster-IP", "External-IP", "Port(s)")
                        for item in items:
                            name = item['metadata']['name']
                            self.resource_names.append(name)
                            svc_type = item['spec'].get('type', 'ClusterIP')
                            cluster_ip = item['spec'].get('clusterIP', 'None')
                            external_ip = 'None'
                            if 'externalIPs' in item['spec']:
                                external_ip = ','.join(item['spec']['externalIPs'])
                            elif svc_type == 'LoadBalancer':
                                ingress = item['status'].get('loadBalancer', {}).get('ingress', [])
                                if ingress:
                                    external_ip = ingress[0].get('ip', ingress[0].get('hostname', 'Pending'))
                                else:
                                    external_ip = 'Pending'
                            
                            ports = []
                            for port in item['spec'].get('ports', []):
                                port_str = f"{port['port']}"
                                if 'targetPort' in port:
                                    port_str += f":{port['targetPort']}"
                                if 'protocol' in port:
                                    port_str += f"/{port['protocol']}"
                                ports.append(port_str)
                            ports_str = ','.join(ports) if ports else 'None'
                            
                            table.add_row(name, svc_type, cluster_ip, external_ip, ports_str)
                    
                    elif resource_type == "deployments":
                        table.add_columns("Name", "Ready", "Up-to-date", "Available", "Age")
                        for item in items:
                            name = item['metadata']['name']
                            self.resource_names.append(name)
                            replicas = item['spec'].get('replicas', 0)
                            ready_replicas = item['status'].get('readyReplicas', 0)
                            updated_replicas = item['status'].get('updatedReplicas', 0)
                            available_replicas = item['status'].get('availableReplicas', 0)
                            
                            table.add_row(
                                name, 
                                f"{ready_replicas}/{replicas}",
                                str(updated_replicas),
                                str(available_replicas),
                                "Unknown"  # Simplified for now
                            )
                    
                    else:  # configmaps, secrets, or other resources
                        table.add_columns("Name", "Data", "Age")
                        for item in items:
                            name = item['metadata']['name']
                            self.resource_names.append(name)
                            data_count = len(item.get('data', {}))
                            table.add_row(name, str(data_count), "Unknown")
                else:
                    table.add_columns("Message")
                    table.add_row(f"No {resource_type} found in namespace {self.namespace}")
            else:
                table.add_columns("Error")
                table.add_row(f"Error: {stderr.decode()}")
                
        except Exception as e:
            table = self.query_one("#resources-table", DataTable)
            table.clear(columns=True)
            table.add_columns("Error")
            table.add_row(f"Error loading {resource_type}: {str(e)}")
        finally:
            table.loading = False
    
    @on(Button.Pressed)
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        resource_map = {
            "btn-pods": "pods",
            "btn-services": "services", 
            "btn-deployments": "deployments",
            "btn-configmaps": "configmaps",
            "btn-secrets": "secrets"
        }
        
        if event.button.id in resource_map:
            await self.load_resources(resource_map[event.button.id])
    
    def action_back(self) -> None:
        self.app.pop_screen()
    
    def action_quit(self) -> None:
        self.app.exit()
    
    async def action_refresh(self) -> None:
        await self.load_resources(self.current_resource)
    
    async def action_show_pods(self) -> None:
        await self.load_resources("pods")
    
    async def action_show_services(self) -> None:
        await self.load_resources("services")
    
    async def action_show_deployments(self) -> None:
        await self.load_resources("deployments")
    
    async def action_show_configmaps(self) -> None:
        await self.load_resources("configmaps")
    
    async def action_show_secrets(self) -> None:
        await self.load_resources("secrets")


class K8sDashboard(App):
    """Main Kubernetes Dashboard Application"""
    
    TITLE = "Kubernetes Dashboard"
    CSS = """
    .container {
        padding: 1;
        height: 100%;
    }
    
    .title {
        text-align: center;
        text-style: bold;
        margin: 1;
        color: $accent;
    }
    
    .subtitle {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }
    
    .help {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    
    .resource-buttons {
        height: 3;
        margin: 1;
    }
    
    ListView {
        height: 1fr;
        margin: 1;
    }
    
    DataTable {
        height: 1fr;
        margin: 1;
    }
    
    Button {
        margin-right: 1;
    }
    
    .modal-container {
        background: $panel;
        border: thick $accent;
        width: 80%;
        height: 80%;
        margin: 2;
        padding: 1;
    }
    
    .modal-title {
        text-style: bold;
        color: $accent;
        text-align: center;
        margin-bottom: 1;
    }
    
    .modal-content {
        height: 1fr;
        overflow-y: auto;
        background: $surface;
        color: $text;
        padding: 1;
        border: solid $primary;
    }
    
    .modal-help {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]
    
    def __init__(self):
        super().__init__()
        self.selected_context = None
    
    async def on_mount(self) -> None:
        """Load Kubernetes contexts when the app starts"""
        await self.load_contexts()
    
    async def load_contexts(self) -> None:
        """Load available Kubernetes contexts"""
        try:
            result = await asyncio.create_subprocess_exec(
                "kubectl", "config", "get-contexts", "-o", "name",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                contexts = [ctx.strip() for ctx in stdout.decode().split('\n') if ctx.strip()]
                
                # Get current context
                current_result = await asyncio.create_subprocess_exec(
                    "kubectl", "config", "current-context",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                current_stdout, _ = await current_result.communicate()
                current_context = current_stdout.decode().strip() if current_result.returncode == 0 else ""
                
                if contexts:
                    self.push_screen(ContextSelectionScreen(contexts, current_context))
                else:
                    self.exit(message="No Kubernetes contexts found. Please configure kubectl first.")
            else:
                self.exit(message=f"Error loading contexts: {stderr.decode()}")
                
        except Exception as e:
            self.exit(message=f"Error: {str(e)}. Make sure kubectl is installed and configured.")
    
    def action_quit(self) -> None:
        self.exit()


def main():
    """Main entry point"""
    app = K8sDashboard()
    app.run()


if __name__ == "__main__":
    main()
