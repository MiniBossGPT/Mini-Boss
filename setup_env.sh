#!/bin/bash

git submodule update --init --recursive

TEMPLATE_FILE="auto-gpt/.env.template"
TARGET_FILE="auto-gpt/.env"
cp "${TEMPLATE_FILE}" "${TARGET_FILE}"

while IFS='=' read -r key default_value; do
    if [[ ${key} != \#* ]]; then
        echo "Please enter a value for ${key} (default: ${default_value}):"
        read user_value
        if [[ -z "${user_value}" ]]; then
            user_value="${default_value}"
        fi
        sed -i "s|^${key}=${default_value}|${key}=${user_value}|" "${TARGET_FILE}"
    fi
done < "${TEMPLATE_FILE}"

cp "${TARGET_FILE}" .env
