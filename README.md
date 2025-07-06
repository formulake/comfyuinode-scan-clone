# comfyuinode-scan-clone
A simple external application for Windows that allows you to scan an existing custom_nodes directory and generate a list of the nodes installed. A simple cloner uses the list to clone the nodes into a fresh directory. The advanced cloner allows you to select the nodes from the list that you want to clone.

Key Features
Node Scanner
Scans custom_nodes for .git/config or pyproject.toml
Exports GitHub repo URLs as .txt or .md
Optional: include or exclude folder names

Simple Cloner
Upload a .txt or .md file
Clones all repos
Displays real-time clone status, ETA, and duration

Advanced Cloner
Upload .txt or .md file
Displays checkboxes of repo names
Select some or all
