$env:JAVA_HOME = "C:\Program Files\Java\jdk-12"

$env:PATH = "$env:JAVA_HOME\bin;" + ($env:PATH -replace "[^;]*\\Java\\[^;]*\\bin;?", "")

