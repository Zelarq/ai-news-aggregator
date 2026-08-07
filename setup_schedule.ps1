$TaskName = "AINewsDigest"
$WorkspacePath = "D:\collage\ai-news-aggregator"
$BatPath = "$WorkspacePath\run_agent.bat"

Write-Host "Setting up Windows Task Scheduler for $TaskName..."

# The action to run the batch file
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c ""$BatPath""" -WorkingDirectory $WorkspacePath

# Trigger it daily at 8:00 AM
$Trigger = New-ScheduledTaskTrigger -Daily -At 8:00AM

# Settings to ensure it runs smoothly (even on laptop battery, and start if missed)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register the task (overwrites if it already exists)
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Runs the Daily AI News Digest agent automatically." -Force

Write-Host "Task successfully registered to run daily at 8:00 AM!"
