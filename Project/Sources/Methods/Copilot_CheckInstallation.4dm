//%attributes = {}
// Copilot_CheckInstallation
// Example: Check if GitHub Copilot CLI is installed and accessible

var $copilot : cs:C1710.CopilotCLI
var $check : Object
var $message : Text

// Create copilot instance
$copilot:=cs:C1710.CopilotCLI.new()

// Check installation
$check:=$copilot.checkInstallation()

// Build message
If ($check.installed)

	$message:="✅ GitHub Copilot CLI is installed!\n\n"
	$message:=$message+"Working Directory: "+$copilot.workingDirectory+"\n"
	$message:=$message+"Copilot Path: "+$copilot.copilotPath+"\n\n"
	$message:=$message+"Help Output:\n"+$check.version

Else

	$message:="❌ GitHub Copilot CLI is NOT installed or not accessible.\n\n"

	If ($check.errors#Null:C1517)
		var $error : Object
		For each ($error; $check.errors)
			$message:=$message+"Error: "+$error.message+"\n"
		End for each
	Else
		$message:=$message+"Error: "+$check.error+"\n"
	End if

	$message:=$message+"\n"
	$message:=$message+"To install GitHub Copilot CLI:\n"
	$message:=$message+"  npm install -g @github/copilot\n\n"
	$message:=$message+"Requirements:\n"
	$message:=$message+"  - Node.js v22 or higher\n"
	$message:=$message+"  - npm v10 or higher\n"
	$message:=$message+"  - Active GitHub Copilot subscription"

End if

// Display result
ALERT:C41($message)

// Optional: Copy to clipboard
SET TEXT TO PASTEBOARD:C523($message)
