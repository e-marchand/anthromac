// CopilotCLI - Wrapper class for GitHub Copilot CLI using 4D System Worker
// Allows using GitHub Copilot from 4D on the current database folder

Class constructor

	// System Worker reference
	This:C1470.worker:=Null:C1517
	This:C1470.workerId:=""

	// Configuration properties
	This:C1470.workingDirectory:=""
	This:C1470.copilotPath:="copilot"  // Command path, can be overridden
	This:C1470.githubToken:=""  // Optional GitHub token for authentication

	// Command options
	This:C1470.allowedTools:=[]  // Collection of allowed tools
	This:C1470.deniedTools:=[]  // Collection of denied tools
	This:C1470.allowAllTools:=False:C215  // Allow all tools without prompts
	This:C1470.showBanner:=False:C215  // Show animated banner

	// Output handling
	This:C1470.output:=""
	This:C1470.errorOutput:=""
	This:C1470.isRunning:=False:C215

	// Set default working directory to database folder
	This:C1470.workingDirectory:=Convert path system to POSIX:C1106(Get 4D folder:C485(Database folder:K5:14))


// Configure the working directory
Function setWorkingDirectory($path : Text) : cs:C1710.CopilotCLI

	This:C1470.workingDirectory:=$path
	return This:C1470


// Set GitHub token for authentication
Function setGitHubToken($token : Text) : cs:C1710.CopilotCLI

	This:C1470.githubToken:=$token
	return This:C1470


// Set custom copilot command path
Function setCopilotPath($path : Text) : cs:C1710.CopilotCLI

	This:C1470.copilotPath:=$path
	return This:C1470


// Add allowed tool (can use glob patterns)
Function allowTool($tool : Text) : cs:C1710.CopilotCLI

	If (This:C1470.allowedTools.indexOf($tool)<0)
		This:C1470.allowedTools.push($tool)
	End if
	return This:C1470


// Add denied tool (can use glob patterns)
Function denyTool($tool : Text) : cs:C1710.CopilotCLI

	If (This:C1470.deniedTools.indexOf($tool)<0)
		This:C1470.deniedTools.push($tool)
	End if
	return This:C1470


// Clear all tool permissions
Function clearToolPermissions() : cs:C1710.CopilotCLI

	This:C1470.allowedTools:=[]
	This:C1470.deniedTools:=[]
	This:C1470.allowAllTools:=False:C215
	return This:C1470


// Allow all tools without asking
Function setAllowAllTools($allow : Boolean) : cs:C1710.CopilotCLI

	This:C1470.allowAllTools:=$allow
	return This:C1470


// Enable/disable animated banner
Function setBanner($show : Boolean) : cs:C1710.CopilotCLI

	This:C1470.showBanner:=$show
	return This:C1470


// Build command with options
Function _buildCommand($baseCommand : Text; $additionalArgs : Collection) : Text

	var $command : Text
	var $arg : Text

	$command:=This:C1470.copilotPath

	If ($baseCommand#"")
		$command:=$command+" "+$baseCommand
	End if

	// Add banner flag if enabled
	If (This:C1470.showBanner)
		$command:=$command+" --banner"
	End if

	// Add tool permissions
	If (This:C1470.allowAllTools)
		$command:=$command+" --allow-all-tools"
	End if

	For each ($arg; This:C1470.allowedTools)
		$command:=$command+" --allow-tool \""+$arg+"\""
	End for each

	For each ($arg; This:C1470.deniedTools)
		$command:=$command+" --deny-tool \""+$arg+"\""
	End for each

	// Add additional arguments
	If ($additionalArgs#Null:C1517)
		For each ($arg; $additionalArgs)
			$command:=$command+" "+$arg
		End for each
	End if

	return $command


// Build environment variables for the worker
Function _buildEnvironment() : Object

	var $env : Object

	$env:={}

	// Add GitHub token if set
	If (This:C1470.githubToken#"")
		$env.GH_TOKEN:=This:C1470.githubToken
	End if

	return $env


// Execute copilot with a prompt (programmatic mode)
Function executePrompt($prompt : Text; $agent : Text) : Object

	var $result : Object
	var $command : Text
	var $args : Collection

	$result:={success: False:C215; output: ""; error: ""}

	Try

		If ($prompt="")
			throw "Prompt cannot be empty"
		End if

		$args:=[]
		$args.push("--prompt \""+$prompt+"\"")

		// Add agent if specified
		If ($agent#"")
			$args.push("--agent="+$agent)
		End if

		$command:=This:C1470._buildCommand(""; $args)

		// Execute the command
		$result:=This:C1470._executeCommand($command)

	Catch

		$result.errors:=Last errors:C1799

	End try

	return $result


// Start interactive session
Function startInteractive() : Object

	var $result : Object
	var $command : Text

	$result:={success: False:C215; output: ""; error: ""}

	Try

		$command:=This:C1470._buildCommand(""; Null:C1517)
		$result:=This:C1470._executeCommand($command)

	Catch

		$result.errors:=Last errors:C1799

	End try

	return $result


// Resume a previous session
Function resume() : Object

	var $result : Object
	var $command : Text
	var $args : Collection

	$result:={success: False:C215; output: ""; error: ""}

	Try

		$args:=[]
		$args.push("--resume")

		$command:=This:C1470._buildCommand(""; $args)
		$result:=This:C1470._executeCommand($command)

	Catch

		$result.errors:=Last errors:C1799

	End try

	return $result


// Continue the most recent session
Function continueSession() : Object

	var $result : Object
	var $command : Text
	var $args : Collection

	$result:={success: False:C215; output: ""; error: ""; workerId: ""}

	Try

		$args:=[]
		$args.push("--continue")

		$command:=This:C1470._buildCommand(""; $args)
		$result:=This:C1470._executeCommand($command)

	Catch

		$result.errors:=Last errors:C1799

	End try

	return $result


// Get help information
Function getHelp($topic : Text) : Object

	var $result : Object
	var $command : Text
	var $args : Collection

	$result:={success: False:C215; output: ""; error: ""}

	Try

		$args:=[]

		If ($topic="")
			$command:=This:C1470._buildCommand("help"; Null:C1517)
		Else
			$command:=This:C1470._buildCommand("help "+$topic; Null:C1517)
		End if

		$result:=This:C1470._executeCommand($command)

	Catch

		$result.errors:=Last errors:C1799

	End try

	return $result


// Execute command using System Worker
Function _executeCommand($command : Text) : Object

	var $result : Object
	var $env : Object
	var $workerId : Text

	$result:={success: False:C215; output: ""; error: ""; workerId: ""}

	Try

		$env:=This:C1470._buildEnvironment()

		// Create unique worker ID
		$workerId:="copilot_"+String:C10(Generate UUID:C1066)

		// Start the system worker (synchronous execution)
		This:C1470.worker:=4D:C1709.SystemWorker.new($command; {currentDirectory: This:C1470.workingDirectory; environmentVariables: $env})
		This:C1470.workerId:=$workerId
		This:C1470.isRunning:=True:C214

		// Wait for completion and collect output
		This:C1470.worker.wait()

		$result.output:=This:C1470.worker.response
		$result.error:=This:C1470.worker.errors
		$result.success:=(This:C1470.worker.exitCode=0)
		$result.exitCode:=This:C1470.worker.exitCode
		$result.workerId:=$workerId

		This:C1470.isRunning:=False:C215

	Catch

		$result.errors:=Last errors:C1799
		This:C1470.isRunning:=False:C215

	End try

	return $result


// Terminate the current worker
Function terminate() : Boolean

	If (This:C1470.worker#Null:C1517)
		This:C1470.worker.terminate()
		This:C1470.isRunning:=False:C215
		return True:C214
	End if

	return False:C215


// Check if copilot is installed and accessible
Function checkInstallation() : Object

	var $result : Object
	var $worker : 4D:C1709.SystemWorker

	$result:={installed: False:C215; version: ""; error: ""}

	Try

		$worker:=4D:C1709.SystemWorker.new(This:C1470.copilotPath+" help")
		$worker.wait()

		If ($worker.exitCode=0)
			$result.installed:=True:C214
			$result.version:=$worker.response
		Else
			$result.error:=$worker.errors
		End if

	Catch

		$result.errors:=Last errors:C1799

	End try

	return $result
