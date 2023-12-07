import json

def drop_columns(data):
    # Define the indices of the columns to be dropped (0-based index)
    columns_to_drop = [1,4,6,8]
    
    # Iterate through each item in "segment_sizes_bits" and drop specified columns
    for item in data["segment_sizes_bits"]:
        for col_index in sorted(columns_to_drop, reverse=True):
            del item[col_index]
    
    return data

def edit_json_file(file_path):
    with open(file_path, 'r') as json_file:
        # Load JSON data
        json_data = json.load(json_file)

    # Modify the JSON data by dropping specified columns
    edited_data = drop_columns(json_data)

    with open(file_path, 'w') as json_file:
        # Write the edited data back to the same file
        json.dump(edited_data, json_file, indent=2)

# Replace 'your_json_file.json' with the actual path to your JSON file
edit_json_file('bbb.json')
