#!/bin/bash

git clone --recursive -b stable https://github.com/Significant-Gravitas/Auto-GPT
cp auto-gpt/.env.template auto-gpt/.env && cp auto-gpt/.env.template .env

