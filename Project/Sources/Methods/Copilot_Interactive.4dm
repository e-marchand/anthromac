//%attributes = {}
// Copilot_Interactive
// Example: Start an interactive GitHub Copilot CLI session

var $copilot : cs:C1710.CopilotCLI
var $result : Object
var $choice : Integer

// Ask user which mode to use
$choice:=Request:C163("Choose mode:\n1 = New Session\n2 = Resume Previous\n3 = Continue Recent"; "1")

If (OK=1)

	// Create copilot instance
	$copilot:=cs:C1710.CopilotCLI.new()

	// Optional: Configure settings
	$copilot.setAllowAllTools(True:C214)  // Allow all tools without prompting
	$copilot.setBanner(True:C214)  // Show animated banner

	// Optional: Configure tool permissions
	// $copilot.allowTool("shell(npm run test:*)")
	// $copilot.denyTool("shell(rm *)")

	// Execute based on choice
	Case of
		: ($choice="1")
			// Start new interactive session
			ALERT:C41("Starting new interactive Copilot session...\n\nNote: This will open in the terminal.")
			$result:=$copilot.startInteractive()

		: ($choice="2")
			// Resume a previous session (will show list to choose from)
			ALERT:C41("Resuming previous Copilot session...\n\nNote: This will open in the terminal.")
			$result:=$copilot.resume()

		: ($choice="3")
			// Continue most recent session
			ALERT:C41("Continuing most recent Copilot session...\n\nNote: This will open in the terminal.")
			$result:=$copilot.continueSession()

		Else
			ALERT:C41("Invalid choice")
			return

	End case

	// Check result
	If ($result.success)
		ALERT:C41("Session completed successfully!")
	Else
		If ($result.errors#Null:C1517)
			var $error : Object
			var $errorMsg : Text
			$errorMsg:=""

			For each ($error; $result.errors)
				$errorMsg:=$errorMsg+$error.message+"\n"
			End for each

			ALERT:C41("Error occurred:\n"+$errorMsg)
		Else
			ALERT:C41("Session failed with exit code "+String:C10($result.exitCode)+"\n\n"+$result.error)
		End if
	End if

End if
