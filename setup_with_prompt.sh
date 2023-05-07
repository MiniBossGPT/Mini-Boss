###!/bin/bash
##
##git submodule update --init --recursive
##
##TEMPLATE_FILE="auto-gpt/.env.template"
##TARGET_FILE="auto-gpt/.envtest"
##cp "${TEMPLATE_FILE}" "${TARGET_FILE}"
##
##while IFS='=' read -r key default_value; do
##    if [[ ${key} != \#* ]]; then
##        echo "Please enter a value for ${key} (default: ${default_value}):"
##        read user_value
##        if [[ -z "${user_value}" ]]; then
##            user_value="${default_value}"
##        fi
##        sed -i "s|^${key}=${default_value}|${key}=${user_value}|" "${TARGET_FILE}"
##    fi
##done < "${TEMPLATE_FILE}"
##
##cp "${TARGET_FILE}" .envtest
#
#
#### option 2 - in progress 05-06-2023
##!/bin/bash
#
## Prompt user for input
#echo "Enter your OpenAI API Key:"
#read OPENAI_API_KEY
#
#echo "Enter the execution temperature (default: 0):"
#read TEMPERATURE
#
#echo "Do you want to use Azure OpenAI? (yes/no, default: no):"
#read USE_AZURE
#
## Set default values if not provided
#TEMPERATURE=${TEMPERATURE:-0}
#USE_AZURE=${USE_AZURE:-no}
#
## Transform yes/no to True/False for USE_AZURE
#if [ "$USE_AZURE" == "yes" ]; then
#    USE_AZURE=True
#else
#    USE_AZURE=False
#fi
#
## Create the .env file
#cat > .env <<EOL
#################################################################################
#### AUTO-GPT - GENERAL SETTINGS
#################################################################################
#
### EXECUTE_LOCAL_COMMANDS - Allow local command execution (Default: False)
### RESTRICT_TO_WORKSPACE - Restrict file operations to workspace ./auto_gpt_workspace (Default: True)
## EXECUTE_LOCAL_COMMANDS=False
## RESTRICT_TO_WORKSPACE=True
#
### USER_AGENT - Define the user-agent used by the requests library to browse website (string)
## USER_AGENT="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
#
### AI_SETTINGS_FILE - Specifies which AI Settings file to use (defaults to ai_settings.yaml)
## AI_SETTINGS_FILE=ai_settings.yaml
#
### AUTHORISE COMMAND KEY - Key to authorise commands
## AUTHORISE_COMMAND_KEY=y
### EXIT_KEY - Key to exit AUTO-GPT
## EXIT_KEY=n
#
#################################################################################
#### LLM PROVIDER
#################################################################################
#
#### OPENAI
### OPENAI_API_KEY - OpenAI API Key (Example: my-openai-api-key)
### TEMPERATURE - Sets temperature in OpenAI (Default: 0)
### USE_AZURE - Use Azure OpenAI or not (Default: False)
#OPENAI_API_KEY=$OPENAI_API_KEY
#TEMPERATURE=$TEMPERATURE
#USE_AZURE=$USE_AZURE
#
#### AZURE
## moved to \`azure.yaml.template\`
#EOL
#
#echo ".env file created successfully."
