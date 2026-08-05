#!/usr/bin/python3

# Converts .json files from Translatewiki into .js files.
#
# Copyright 2013 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import codecs
import glob
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Any

# Ensure compatibility with modern Python features
if sys.version_info < (3, 6):
    raise Exception("This script requires Python 3.6 or higher.")

def main():
    """Generates .js files defining Blockly and Blockly Games messages."""
    print('Starting Message Compilation...')

    # Argument Parsing 
    parser = argparse.ArgumentParser(description='Convert JSON message files to JS message definitions.')
    parser.add_argument('--default_lang',
                        default='en',
                        help='Missing translations will come from this default language.')
    parser.add_argument('--blockly_msg_dir',
                        default=Path('server', 'html', 'third-party', 'blockly', 'msg', 'json'),
                        type=Path,
                        help='Relative directory for Blockly\'s message .json files.')
    parser.add_argument('--blocklygames_msg_dir',
                        default=Path('json'),
                        type=Path,
                        help='Relative directory for Blockly Games\' message .json files.')
    parser.add_argument('--output_dir',
                        default=Path('server', 'html', 'generated', 'msg'),
                        type=Path,
                        help='Relative directory for output .js files.')
    args = parser.parse_args()

    # Create the output directory if it doesn't exist
    args.output_dir.mkdir(parents=True, exist_ok=True)

  
    try:
        blockly_constants_data = read_json_file(args.blockly_msg_dir, 'constants')
        blockly_synonyms_data = read_json_file(args.blockly_msg_dir, 'synonyms')
        blockly_default_data = read_json_file(args.blockly_msg_dir, args.default_lang)
        bg_default_data = read_json_file(args.blocklygames_msg_dir, args.default_lang)
    except FileNotFoundError as e:
        print(f"Error: Missing essential JSON file for default language or constants. Details: {e}")
        sys.exit(1)


    # Use glob with Path to find all language files in the Blockly Games directory.
    language_files = sorted(args.blocklygames_msg_dir.glob('*.json'))
    languages: List[str] = []

    for language_file in language_files:
        # Extract the language code from the filename 
        language = language_file.stem 
        if language == 'qqq':
            continue
        
        # Check if the corresponding Blockly message file exists.
        blockly_lang_path = args.blockly_msg_dir / f'{language}.json'
        if not blockly_lang_path.is_file():
            # Must have both Blockly Games and Blockly message files to proceed.
            print(f"Warning: Skipping language '{language}'. Blockly message file not found at {blockly_lang_path}.")
            continue
            
        languages.append(language)
        
        # --- Generate Output JS File for Current Language 
        output_path = args.output_dir / f'{language}.js'
        print(f"Processing messages for language: {language}")
        
        # Open the output file using codecs.open for explicit UTF-8 encoding
        with codecs.open(output_path, 'w', 'utf-8') as output_file:
            # Write the header
            output_file.write('''// This file was automatically generated. Do not modify.

'use strict';
var BlocklyMsg = {};
var BlocklyGamesMsg = {};

''')

            # 1. Write the Blockly messages.
            write_blockly_messages(output_file, args.blockly_msg_dir, language, 
                                   blockly_default_data, blockly_synonyms_data, blockly_constants_data)

            # 2. Write the Blockly Games messages.
            write_blockly_games_messages(output_file, args.blocklygames_msg_dir, language, bg_default_data)

    print(f'\n Message JS files generated for the following languages: {", ".join(languages)}')


def write_blockly_messages(output_file: Any, blockly_dir: Path, language: str, 
                           default_data: Dict[str, str], synonyms_data: Dict[str, str], 
                           constants_data: Dict[str, str]):
    """Writes Blockly message definitions (translations, synonyms, constants) to the output file."""
    
    try:
        blockly_language_data = read_json_file(blockly_dir, language)
    except FileNotFoundError:
        # Should not happen due to the check in main(), but defensive programming.
        print(f"Error: Blockly language file for '{language}' not found.")
        return

    blockly_msg_dict: Dict[str, str] = {}
    
    # 1a. Write translated messages 
    for name, default_message in default_data.items():
        if name in blockly_language_data:
            message_str = blockly_language_data[name]
            comment = ''
        else:
            message_str = default_message
            comment = '  // untranslated'
            
        message_str = scrub_message(message_str)
        blockly_msg_dict[name] = message_str
        output_file.write(f'BlocklyMsg["{name}"] = "{message_str}";{comment}\n')
    
    output_file.write('\n')
    
    # 1b. Write synonyms 
    for name, alias_name in synonyms_data.items():
        if alias_name in blockly_msg_dict:
             alias_value = blockly_msg_dict[alias_name]
             blockly_msg_dict[name] = alias_value
             output_file.write(f'BlocklyMsg["{name}"] = BlocklyMsg["{alias_name}"]; // Synonym of {alias_name}\n')
        else:

    
            print(f"Warning: Synonym '{name}' references non-existent message '{alias_name}'.")

    output_file.write('\n')
    
    # Write constants 
    for name, message_str in constants_data.items():
        message_str = scrub_message(message_str)
        blockly_msg_dict[name] = message_str
        output_file.write(f'BlocklyMsg["{name}"] = "{message_str}"; // Constant\n')
        
    output_file.write('\n')


def write_blockly_games_messages(output_file: Any, bg_dir: Path, language: str, 
                                 default_data: Dict[str, str]):
    """Writes Blockly Games message definitions (BlocklyGamesMsg["..."] = "...";) to the output file."""
    
    try:
        bg_language_data = read_json_file(bg_dir, language)
    except FileNotFoundError:
        # Should not happen due to the check in main.
        print(f"Error: Blockly Games language file for '{language}' not found.")
        return


    for name, default_message in default_data.items():
        if name in bg_language_data:
            message_str = bg_language_data[name]
            comment = ''
        else:
            message_str = default_message
            comment = '  // untranslated'
            
        message_str = scrub_message(message_str)
        output_file.write(f'BlocklyGamesMsg["{name}"] = "{message_str}";{comment}\n')


def scrub_message(msg: str) -> str:
    """
    Cleans up a message string for use in JavaScript,
    escaping quotes, backslashes, and newlines.
    """
    msg = msg.strip()
    msg = msg.replace('\\', '\\\\')
    msg = msg.replace('\n', '\\n')  
    msg = msg.replace('"', '\\"')  
    return msg


def read_json_file(directory: Path, isoCode: str) -> Dict[str, str]:
    """Reads and parses a JSON message file, removing the @metadata tag."""
    file_path = directory / f'{isoCode}.json'
    
    if not file_path.is_file():
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    # Use codecs.open for reliable UTF-8 reading
    with codecs.open(file_path, 'r', 'utf-8') as json_file:
        data = json.load(json_file)
        
    # Ensure all values are treated as strings 
    if not isinstance(data, dict):
        raise ValueError(f"JSON file '{file_path}' does not contain a valid dictionary.")
        

    if '@metadata' in data:
        del data['@metadata']
        
    return data


if __name__ == '__main__':
    main()
