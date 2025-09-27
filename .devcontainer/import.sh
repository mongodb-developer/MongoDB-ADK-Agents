#!/bin/bash

cd .devcontainer/data
mongorestore --uri mongodb://localhost:27017/grocery_store --drop grocery_store/
