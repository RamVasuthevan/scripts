#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Step 0: Remove the existing export.db and any JSON files, except settings.json
echo "Cleaning up old files..."
rm -f "$SCRIPT_DIR/export.db"
find "$SCRIPT_DIR" -name "*.json" ! -name "settings.json" -exec rm {} \;

# Step 1: Unzip the export file
echo "Unzipping export file..."
unzip -o 03b403637625862e5cdb3a922eda3a495a8caa6aafd5afb62c30327c722d251f-2024-09-25-03-00-49.zip

# Step 2: Insert conversations data (excluding mappings) into conversations table
echo "Inserting main conversation data (without mappings) into conversations table..."
sqlite-utils insert "$SCRIPT_DIR/export.db" conversations "$SCRIPT_DIR/conversations.json" --pk id

# Step 3: Extract and insert mapping data into conversation_mappings table
echo "Extracting and inserting mapping data into conversation_mappings table..."
jq '[.[] | . as $conv | .mapping | to_entries[] | {conversation_id: $conv.id, mapping_id: .key, mapping_data: .value}]' "$SCRIPT_DIR/conversations.json" > "$SCRIPT_DIR/conversation_mappings.json"
sqlite-utils insert "$SCRIPT_DIR/export.db" conversation_mappings "$SCRIPT_DIR/conversation_mappings.json" \
    --pk conversation_id --pk mapping_id
rm "$SCRIPT_DIR/conversation_mappings.json"

# Step 3.5: Add foreign key constraint
echo "Adding foreign key constraint on conversation_id..."
sqlite-utils add-foreign-key "$SCRIPT_DIR/export.db" conversation_mappings conversation_id conversations id

# Step 4: Import other JSON files into export.db
echo "Inserting data from model_comparisons.json with 'id' as primary key..."
sqlite-utils insert "$SCRIPT_DIR/export.db" model_comparisons "$SCRIPT_DIR/model_comparisons.json" --pk id

echo "Inserting data from shared_conversations.json with 'id' as primary key..."
sqlite-utils insert "$SCRIPT_DIR/export.db" shared_conversations "$SCRIPT_DIR/shared_conversations.json" --pk id

echo "Inserting data from user.json with 'id' as primary key..."
sqlite-utils insert "$SCRIPT_DIR/export.db" user "$SCRIPT_DIR/user.json" --pk id

echo "Inserting data from message_feedback.json with 'id' as primary key..."
sqlite-utils insert "$SCRIPT_DIR/export.db" message_feedback "$SCRIPT_DIR/message_feedback.json" --pk id

# Check if all steps were successful
if [ $? -eq 0 ]; then
    echo "All files imported successfully with correct primary and foreign keys set!"
else
    echo "Error: Failed to import and normalize conversations.json"
    exit 1
fi
