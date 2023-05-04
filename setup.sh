#!/bin/bash

git submodule update --init --recursive
cp auto-gpt/.env.template auto-gpt/.env && cp auto-gpt/.env.template .env

