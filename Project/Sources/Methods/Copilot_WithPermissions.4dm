//%attributes = {}
// Copilot_WithPermissions
// Example: Execute Copilot with specific tool permissions

var $copilot : cs:C1710.CopilotCLI
var $result : Object
var $prompt : Text

// Get prompt from user
$prompt:=Request:C163("Enter a prompt that may require tools (e.g., file operations, shell commands):"; "Run npm test and show me the results")

If (OK=1) & ($prompt#"")

	// Create copilot instance
	$copilot:=cs:C1710.CopilotCLI.new()

	// Configure tool permissions

	// Example 1: Allow all tools without prompting (easiest but less safe)
	// $copilot.setAllowAllTools(True)

	// Example 2: Allow specific tools using glob patterns
	$copilot.allowTool("shell(npm run *)")  // Allow all npm run commands
	$copilot.allowTool("shell(git status)")  // Allow git status
	$copilot.allowTool("shell(ls *)")  // Allow ls commands
	$copilot.allowTool("Read")  // Allow file reading
	$copilot.allowTool("Glob")  // Allow file pattern matching

	// Example 3: Deny dangerous tools
	$copilot.denyTool("shell(rm *)")  // Deny file deletion
	$copilot.denyTool("shell(sudo *)")  // Deny sudo commands

	// Execute the prompt
	$result:=$copilot.executePrompt($prompt; "")

	// Handle result
	If ($result.success)

		var $displayText : Text
		$displayText:="=== Copilot Response ===\n\n"
		$displayText:=$displayText+$result.output

		ALERT:C41($displayText)

		// Copy to clipboard
		SET TEXT TO PASTEBOARD:C523($result.output)

	Else

		// Handle error
		If ($result.errors#Null:C1517)
			var $error : Object
			var $errorMsg : Text
			$errorMsg:=""

			For each ($error; $result.errors)
				$errorMsg:=$errorMsg+$error.message+"\n"
			End for each

			ALERT:C41("Error occurred:\n"+$errorMsg)
		Else
			ALERT:C41("Command failed with exit code "+String:C10($result.exitCode)+"\n\n"+$result.error)
		End if

	End if

End if
