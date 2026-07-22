# ProxyDLLGen

Automatic Windows DLL Proxy generator that analyzes existing DLL exports and creates a ready-to-build Visual Studio project.

The tool extracts exported functions from a DLL, generates a `.def` file with export forwarding, copies the original DLL, and creates the required Visual Studio project files (`.vcxproj` and `.sln`).

## Features

- Extracts DLL export table using PE analysis
- Generates `.def` files automatically
- Supports x86 and x64 architectures
- Creates Visual Studio 2022 projects automatically
- Generates DLL Proxy templates
- Supports export forwarding for functions and ordinals

## Requirements

- Windows
- Python 3.10+
- Visual Studio 2022 (for compiling the generated project)
- MSVC Build Tools

## Installation

Clone the repository:

```cmd
git clone https://github.com/SEU_USUARIO/ProxyDLLGen.git
cd ProxyDLLGen
