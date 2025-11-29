# CopilotCLI Class - Usage Guide

A 4D class wrapper for GitHub Copilot CLI using 4D System Worker, allowing you to use GitHub Copilot from 4D on the current database folder.

## Prerequisites

1. **Install GitHub Copilot CLI**:
   ```bash
   npm install -g @github/copilot
   ```

2. **Requirements**:
   - Node.js v22 or higher
   - npm v10 or higher
   - Active GitHub Copilot subscription
   - GitHub authentication (via `gh` CLI or token)

3. **Authentication**:
   - Option 1: Use GitHub CLI: `gh auth login`
   - Option 2: Set environment token via the class (see examples below)

## Class Features

### Properties
- `workingDirectory` - Working directory for copilot (defaults to database folder)
- `copilotPath` - Path to copilot executable (defaults to "copilot")
- `githubToken` - GitHub authentication token (GH_TOKEN)
- `allowedTools` - Collection of allowed tools
- `deniedTools` - Collection of denied tools
- `allowAllTools` - Boolean to allow all tools without prompts
- `showBanner` - Boolean to show animated banner

### Main Methods

#### Configuration Methods
- `setWorkingDirectory($path : Text)` - Set custom working directory
- `setGitHubToken($token : Text)` - Set GitHub authentication token
- `setCopilotPath($path : Text)` - Set custom copilot command path
- `allowTool($tool : Text)` - Add allowed tool (supports glob patterns)
- `denyTool($tool : Text)` - Add denied tool (supports glob patterns)
- `clearToolPermissions()` - Clear all tool permissions
- `setAllowAllTools($allow : Boolean)` - Allow/deny all tools without prompts
- `setBanner($show : Boolean)` - Show/hide animated banner

#### Execution Methods
- `executePrompt($prompt : Text; $agent : Text)` - Execute with a prompt (programmatic mode)
- `startInteractive()` - Start interactive session
- `resume()` - Resume a previous session
- `continueSession()` - Continue the most recent session
- `getHelp($topic : Text)` - Get help information
- `terminate()` - Terminate the current worker
- `checkInstallation()` - Check if copilot is installed

## Usage Examples

### Example 1: Check Installation
```4d
// Check if GitHub Copilot CLI is installed
var $copilot : cs.CopilotCLI
var $check : Object

$copilot:=cs.CopilotCLI.new()
$check:=$copilot.checkInstallation()

If ($check.installed)
    ALERT("GitHub Copilot CLI is installed!")
Else
    ALERT("GitHub Copilot CLI is not installed: "+$check.error)
End if
```

### Example 2: Execute a Simple Prompt
```4d
// Execute a prompt and get the result
var $copilot : cs.CopilotCLI
var $result : Object

$copilot:=cs.CopilotCLI.new()
$result:=$copilot.executePrompt("How do I create a collection in 4D?"; "")

If ($result.success)
    ALERT("Response: "+$result.output)
Else
    ALERT("Error: "+$result.error)
End if
```

### Example 3: Use with Custom Working Directory
```4d
// Execute copilot in a specific directory
var $copilot : cs.CopilotCLI
var $result : Object

$copilot:=cs.CopilotCLI.new()
$copilot.setWorkingDirectory("/path/to/your/project")
$result:=$copilot.executePrompt("List all files in this directory"; "")

If ($result.success)
    TRACE  // View output in debugger
End if
```

### Example 4: Use with GitHub Token Authentication
```4d
// Use with GitHub token for authentication
var $copilot : cs.CopilotCLI
var $result : Object
var $token : Text

$token:="ghp_YourGitHubPersonalAccessToken"

$copilot:=cs.CopilotCLI.new()
$copilot.setGitHubToken($token)
$result:=$copilot.executePrompt("Explain 4D ORDA"; "")

If ($result.success)
    ALERT($result.output)
End if
```

### Example 5: Configure Tool Permissions
```4d
// Allow specific tools, deny others
var $copilot : cs.CopilotCLI
var $result : Object

$copilot:=cs.CopilotCLI.new()

// Allow all npm test scripts using glob pattern
$copilot.allowTool("shell(npm run test:*)")

// Deny specific dangerous commands
$copilot.denyTool("shell(rm *)")

// Or allow all tools without prompting
// $copilot.setAllowAllTools(True)

$result:=$copilot.executePrompt("Run tests"; "")
```

### Example 6: Use with Custom Agent
```4d
// Execute with a custom agent
var $copilot : cs.CopilotCLI
var $result : Object

$copilot:=cs.CopilotCLI.new()
$result:=$copilot.executePrompt("Refactor this code block"; "refactor-agent")

If ($result.success)
    ALERT("Refactoring suggestions: "+$result.output)
End if
```

### Example 7: Continue Most Recent Session
```4d
// Continue the most recent copilot session
var $copilot : cs.CopilotCLI
var $result : Object

$copilot:=cs.CopilotCLI.new()
$result:=$copilot.continueSession()

If ($result.success)
    ALERT("Session continued successfully")
End if
```

### Example 8: Get Help Information
```4d
// Get help for different topics
var $copilot : cs.CopilotCLI
var $result : Object

$copilot:=cs.CopilotCLI.new()

// General help
$result:=$copilot.getHelp("")

// Specific topics
$result:=$copilot.getHelp("config")
$result:=$copilot.getHelp("environment")
$result:=$copilot.getHelp("logging")
$result:=$copilot.getHelp("permissions")

If ($result.success)
    ALERT($result.output)
End if
```

### Example 9: Method Chaining
```4d
// Use fluent interface for configuration
var $copilot : cs.CopilotCLI
var $result : Object

$copilot:=cs.CopilotCLI.new()
$copilot.\
    setWorkingDirectory(Convert path system to POSIX(Get 4D folder(Database folder))).\
    setAllowAllTools(True).\
    setBanner(True)

$result:=$copilot.executePrompt("Analyze this 4D database structure"; "")
```

### Example 10: Database Analysis
```4d
// Analyze the current 4D database
var $copilot : cs.CopilotCLI
var $result : Object
var $prompt : Text

$copilot:=cs.CopilotCLI.new()

// Working directory is already set to database folder by default
$prompt:="List all .4dm files in the Project/Sources/Classes directory and explain their purpose"

$result:=$copilot.executePrompt($prompt; "")

If ($result.success)
    ALERT("Analysis: "+$result.output)
Else
    ALERT("Error: "+$result.error)
End if
```

## Return Object Structure

All execution methods return an Object with the following structure:

```4d
{
    success: Boolean,      // True if command executed successfully
    output: Text,          // Standard output from copilot
    error: Text,           // Error output if any
    exitCode: Integer,     // Exit code from the process
    workerId: Text,        // Unique worker ID
    errors: Collection     // Collection of error objects (if exception occurred)
}
```

## Available Copilot CLI Options (Reference)

### Command-Line Flags
- `--prompt <text>` - Execute with a single prompt (programmatic mode)
- `--resume` - Resume a previous session
- `--continue` - Continue the most recent session
- `--agent=<name>` - Use a custom agent
- `--banner` - Show animated banner
- `--allow-tool <tool>` - Allow specific tool (supports glob patterns)
- `--deny-tool <tool>` - Deny specific tool (supports glob patterns)
- `--allow-all-tools` - Allow all tools without prompting

### Slash Commands (Interactive Mode)
- `/login` - Authenticate with GitHub
- `/model` - Switch between AI models
- `/usage` - Show usage statistics
- `/delegate` - Delegate to Copilot coding agent
- `/share` - Save session as Markdown or gist
- `/feedback` - Submit feedback

### Environment Variables
- `GH_TOKEN` or `GITHUB_TOKEN` - GitHub Personal Access Token

## Error Handling

Always check the `success` property of the result object:

```4d
var $copilot : cs.CopilotCLI
var $result : Object

$copilot:=cs.CopilotCLI.new()
$result:=$copilot.executePrompt("My prompt"; "")

If ($result.success)
    // Handle success
    ALERT($result.output)
Else
    // Handle error
    If ($result.errors#Null)
        // Exception occurred
        var $error : Object
        For each ($error; $result.errors)
            ALERT("Error: "+$error.message)
        End for each
    Else
        // Command failed
        ALERT("Command failed with exit code "+String($result.exitCode))
        ALERT("Error output: "+$result.error)
    End if
End if
```

## Notes

1. The working directory defaults to the current 4D database folder
2. All methods that modify configuration return `This` for method chaining
3. The class uses synchronous execution - the method waits for copilot to finish
4. Each quota request reduces your monthly premium request count by one
5. Requires active GitHub Copilot subscription

## Sources

- [Using GitHub Copilot CLI - GitHub Docs](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/use-copilot-cli)
- [GitHub Copilot CLI Repository](https://github.com/github/copilot-cli)
- [About GitHub Copilot CLI - GitHub Docs](https://docs.github.com/en/copilot/concepts/agents/about-copilot-cli)
