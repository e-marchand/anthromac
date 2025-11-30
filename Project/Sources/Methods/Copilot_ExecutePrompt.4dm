//%attributes = {}
// Copilot_ExecutePrompt
// Example: Execute a prompt with GitHub Copilot CLI

var $copilot : cs:C1710.CopilotCLI
var $result : Object
var $prompt : Text
var $agent : Text

// Define your prompt
$prompt:=Request:C163("Enter your prompt for GitHub Copilot:"; "How do I create a collection in 4D?")

If (OK=1) & ($prompt#"")

	// Optional: Specify a custom agent (leave empty for default)
	$agent:=""  // Examples: "refactor-agent", "code-review-agent", etc.

	// Create copilot instance
	$copilot:=cs:C1710.CopilotCLI.new()

	// Optional: Configure settings
	// $copilot.setAllowAllTools(True)
	// $copilot.setBanner(True)

	// Execute the prompt
	$result:=$copilot.executePrompt($prompt; $agent)

	// Handle the result
	If ($result.success)

		// Display the output
		ALERT:C41("Copilot Response:\n\n"+$result.output)

		// Optional: Copy to clipboard
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
