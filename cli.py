#!/usr/bin/env python3
"""
Kubernetes Dashboard - A Textual-based TUI for managing Kubernetes resources
"""

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual.widgets import Header, Footer, Button, Static, ListView, ListItem, Label, Select, DataTable
from textual.screen import Screen
from textual.binding import Binding
from textual import on
import asyncio
import subprocess
import json
from typing import List, Dict, Any, Optional


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
            Static("\nPress number keys to switch resources, r to refresh, Esc to go back, q to quit", classes="help"),
            classes="container"
        )
        yield Footer()
    
    async def on_mount(self) -> None:
        await self.load_resources("pods")
    
    async def load_resources(self, resource_type: str) -> None:
        try:
            self.current_resource = resource_type
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
