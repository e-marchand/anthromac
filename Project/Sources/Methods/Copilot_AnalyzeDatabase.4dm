//%attributes = {}
// Copilot_AnalyzeDatabase
// Example: Use Copilot to analyze the current 4D database structure

var $copilot : cs:C1710.CopilotCLI
var $result : Object
var $prompt : Text
var $choice : Integer
var $prompts : Collection

// Define analysis prompts
$prompts:=[]
$prompts.push({title: "List Classes"; prompt: "List all .4dm files in Project/Sources/Classes/ and briefly describe what each class does based on the code"})
$prompts.push({title: "List Methods"; prompt: "List all .4dm files in Project/Sources/Methods/ and categorize them by purpose"})
$prompts.push({title: "Project Structure"; prompt: "Analyze the Project/Sources directory structure and explain the organization"})
$prompts.push({title: "Code Quality"; prompt: "Review the 4D code in this project and suggest improvements for code quality and best practices"})
$prompts.push({title: "Custom Prompt"; prompt: ""})

// Build choice dialog
var $choiceText : Text
var $i : Integer
$choiceText:="Choose analysis type:\n\n"

For ($i; 0; $prompts.length-1)
	$choiceText:=$choiceText+String:C10($i+1)+" = "+$prompts[$i].title+"\n"
End for

$choice:=Request:C163($choiceText; "1")

If (OK=1)

	var $index : Integer
	$index:=Num:C11($choice)-1

	If ($index>=0) & ($index<$prompts.length)

		// Get the prompt
		If ($prompts[$index].title="Custom Prompt")
			$prompt:=Request:C163("Enter your custom analysis prompt:"; "Analyze this 4D database")
			If (OK=0) | ($prompt="")
				return
			End if
		Else
			$prompt:=$prompts[$index].prompt
		End if

		// Create copilot instance
		$copilot:=cs:C1710.CopilotCLI.new()

		// Working directory is already set to database folder by default
		// But you can override it if needed:
		// $copilot.setWorkingDirectory("/path/to/specific/folder")

		// Allow file operations
		$copilot.setAllowAllTools(True:C214)

		// Show progress
		ALERT:C41("Analyzing database with Copilot...\n\nPrompt: "+$prompt+"\n\nThis may take a moment.")

		// Execute the analysis
		$result:=$copilot.executePrompt($prompt; "")

		// Handle result
		If ($result.success)

			var $displayText : Text
			$displayText:="=== Database Analysis ===\n\n"
			$displayText:=$displayText+"Prompt: "+$prompt+"\n\n"
			$displayText:=$displayText+"--- Response ---\n\n"
			$displayText:=$displayText+$result.output

			// Display in alert (for short responses)
			// For longer responses, consider writing to a file or displaying in a form
			If (Length:C16($displayText)>1000)
				// Save to file if response is long
				var $filePath : Text
				$filePath:=System folder:C487(Desktop:K41:16)+"Copilot_Analysis_"+String:C10(Current date:C33; ISO date GMT:K1:10; Current time:C178)+".txt"
				TEXT TO DOCUMENT:C1237($filePath; $displayText)
				ALERT:C41("Analysis complete!\n\nResponse is too long to display.\nSaved to: "+$filePath)
				OPEN URL:C673($filePath)
			Else
				ALERT:C41($displayText)
			End if

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
				ALERT:C41("Analysis failed with exit code "+String:C10($result.exitCode)+"\n\n"+$result.error)
			End if

		End if

	Else
		ALERT:C41("Invalid choice")
	End if

End if
