## Hi there 👋

Welcome to Arkitekt organization! Arkitekt is a platform and framework for modern bioimage analysis and its workflows. It provides solutions to create and deploy user-friendly bioimage analysis workflows utilizing your bioimage app ecosystem, exisiting code and infrastructure. Arkitekt follows the mantra of "bring your own tools" and will only interface as a middleman with you and your tools, managing only the data as well as the flow and orchestration of your analysis. Please find our documentation at [https://arkitekt.live](https://arkitekt.live)

## Our Projects

This organization hosts a multitude of projects that make up the Arkitekt framework. We divide our organization in three main sections:

- Arkitekt Core/Server
- Arkitekt SDK
- [Arktitekt Apps](https://github.com/arkitektio-apps)

### Arkitekt Core

The heart of our platform, containing essential services required for both standard and custom configurations of the Arkitekt platform. Arkitket Core
are all standalone webservices.

### Services
- **Lok**: Authorization and Authentication service.
- **Rekuest**: Node Repository and Task-Assignment.
- **Port**: Virtualization of plugin apps.
- **Mikro**: Microscopy Data Management.
- **Fluss**: Workflow management.

### GUI Clients
- **Orkestrator**: The standard Arkitekt platform client, available as both a desktop and web app.

### Management Tools
- **Konstruktor**: The management tool for installing and administering the Arkitekt platform.

### Arkitekt SDK

A suite of tools for developing apps and plugins for the Arkitekt platform, available in Python and partially in JavaScript/TypeScript (restricted to React framework).

#### Python SDK
Includes tools for app and plugin development with a comprehensive global documentation and individual repository documentation. Managed with poetry.

- **Meta Packages**:
  - `arkitekt`: A comprehensive package including all Arkitekt SDK tools for Python and the arkitekt CLI tool.
- **Core Libraries**:
  - `rekuest`, `mikro`, `fluss`, `unlok`, `port`, `reaktion`: Clients and schedulers for various Arkitekt services with convenience methods.
- **Supporting Libraries**:
  - `fakts`, `herre`, `turms`, `rath`, `koil`: Provide essential functionality and facilitate the integration of the Arkitekt SDK.
 
### Javascript/Typescript SDK
Includes tools for app and plugin development with a comprehensive global documentation and individual repository documentation. Managed with poetry.

- **Meta Packages**:
  - `arkitekt-ts`: A comprehensive package including all Arkitekt SDK tools for Typescript.
- **Core Libraries**:
  - `rekuest-ts`, `mikro-ts`, `fluss-ts`, `unlok-ts`, `port-ts`, `reaktion-ts`: Clients and schedulers for various Arkitekt services with convenience methods.
- **Supporting Libraries**:
  - `fakts-ts`, `herre-ts`:  Provide essential functionality and facilitate the integration of the Arkitekt SDK.


## Getting Involved

Interested in contributing to Arkitekt? We welcome collaboration and contributions from the community! Here's how you can get involved:

- **Explore**: Browse our [documentation](https://arkitekt.live) and see where you might want to contribute.
- **Issue Tracking**: Found a bug or have a feature
