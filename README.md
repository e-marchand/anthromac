# anthromac

4D utility classes and tools for enhancing development workflows.

## CopilotCLI Class

A 4D class wrapper for GitHub Copilot CLI using 4D System Worker. This allows you to use GitHub Copilot directly from 4D on your current database folder.

### Features

- Execute GitHub Copilot CLI commands from 4D
- Support for programmatic mode with prompts
- Interactive session management
- Tool permission configuration
- Working directory configuration (defaults to database folder)
- GitHub token authentication support
- Method chaining for fluent configuration

### Quick Start

```4d
// Simple usage
var $copilot : cs.CopilotCLI
var $result : Object

$copilot:=cs.CopilotCLI.new()
$result:=$copilot.executePrompt("How do I create a collection in 4D?"; "")

If ($result.success)
    ALERT($result.output)
End if
```

### Sample Methods

The project includes ready-to-use example methods in the "Copilot Examples" folder:

- **Copilot_CheckInstallation** - Verify GitHub Copilot CLI is installed and accessible
- **Copilot_ExecutePrompt** - Execute a simple prompt with custom input
- **Copilot_Interactive** - Start interactive sessions (new/resume/continue)
- **Copilot_AnalyzeDatabase** - Analyze your 4D database with predefined prompts
- **Copilot_WithPermissions** - Execute with configured tool permissions

Simply run any of these methods from 4D to see the CopilotCLI class in action!

### Documentation

See [COPILOT_CLI_USAGE.md](COPILOT_CLI_USAGE.md) for complete usage examples and documentation.

### Prerequisites

- Node.js v22 or higher
- npm v10 or higher
- GitHub Copilot CLI installed: `npm install -g @github/copilot`
- Active GitHub Copilot subscription

## Project Structure

```
Project/
└── Sources/
    ├── Classes/
    │   └── CopilotCLI.4dm              # GitHub Copilot CLI wrapper class
    ├── Methods/
    │   ├── Copilot_CheckInstallation.4dm
    │   ├── Copilot_ExecutePrompt.4dm
    │   ├── Copilot_Interactive.4dm
    │   ├── Copilot_AnalyzeDatabase.4dm
    │   └── Copilot_WithPermissions.4dm
    └── folders.json                    # Method organization
```

## License

MIT