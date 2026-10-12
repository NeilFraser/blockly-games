#!/usr/bin/python
# Compresses the files for one game into a single JavaScript file.
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

# This script generates two files:
#   compressed.js
#   uncompressed.js
# The compressed file is a concatenation of all the relevant JavaScript which
# has then been run through Google's Closure Compiler.
# The uncompressed file is a script that loads in each JavaScript file
# one by one.  This takes much longer for a browser to load, but is useful
# when debugging code since line numbers are meaningful and variables haven't
# been renamed.  The uncompressed file also allows for a faster development
# cycle since there is no need to rebuild or recompile, just reload.

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List

# Check Python version
if sys.version_info < (3, 6):
    raise Exception("This script requires Python 3.6 or higher.")

# Define a warning message for all the generated files.
WARNING = '// Automatically generated file. Do not edit!\n'

# Global variables to store message names (used across functions)
blocklyMessageNames: List[str] = []
blocklyGamesMessageNames: List[str] = []

def main(gameName: str):
    """
    Manages the compression and language file filtering process for the specified game.
    """
    global blocklyMessageNames, blocklyGamesMessageNames
    
    print(f'🤖 Starting Build Process for {gameName.title()}...')

    # Define paths using Path objects for cross-OS compatibility
    game_path = Path('server/html') / gameName
    generated_path = game_path / 'generated'

    # Create necessary directories
    try:
        generated_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"Error: Failed to create necessary directories: {e}")
        sys.exit(1)

    # Perform compression first
    generate_uncompressed(gameName, game_path, generated_path)
    generate_compressed(gameName, game_path, generated_path)
    
    # Filter messages based on the compiled JS file
    filterMessages(gameName, generated_path)

    # Extract the list of supported languages from boot.js.
    langs = get_supported_languages()

    # Generate language files for each supported language
    for lang in langs:
        language(gameName, lang, generated_path)
    
    print(f"\n✅ Build Process for {gameName.title()} Completed.")

def get_supported_languages() -> List[str]:
    """
    Extracts the list of supported languages from common/boot.js.
    """
    boot_file = Path('server/html/common/boot.js')
    if not boot_file.exists():
        raise FileNotFoundError(f"Error: boot.js not found at {boot_file}")

    print(f"🌍 Retrieving Supported Languages...")
    
    try:
        js = boot_file.read_text()
        # Find the BlocklyGamesLanguages array definition
        m = re.search(r'\[\'BlocklyGamesLanguages\'\] = (\[[-,\'\s\w]+\])', js)
        
        if not m:
            raise Exception("Cannot find BlocklyGamesLanguages definition in boot.js")
        
        # Parse the JSON array
        langs_str = m.group(1).replace("'", '"')
        return json.loads(langs_str)
    except Exception as e:
        print(f"Error: Failed to extract languages: {e}")
        sys.exit(1)


def filterMessages(gameName: str, generated_path: Path):
    """
    Filters Blockly and Blockly Games messages based on usage within the compressed JS file.
    Updates global blocklyMessageNames and blocklyGamesMessageNames lists.
    """
    global blocklyMessageNames, blocklyGamesMessageNames
    
    compressed_file = generated_path / 'compressed.js'
    if not compressed_file.exists():
        print(f"Error: compressed.js not found. Compilation may have failed: {compressed_file}")
        return

    # Read the compressed code
    js = compressed_file.read_text()

    # Get 'en' messages (assuming it contains all keys)
    msgs = getMessages('en')
    
    # Regex patterns to find message definitions
    blockly_re = re.compile(r'BlocklyMsg\["([^"]+)"\] = ')
    bg_re = re.compile(r'BlocklyGamesMsg\["([^"]+)"\] = ')

    for msg in msgs:
        # Check for Blockly messages
        m = blockly_re.search(msg)
        if m:
            key = m.group(1)
            # Check for different usage forms in the compiled code: quoted, dot notation, or %{BKY_...}
            if (f'"{key}"' in js or
                f'.{key}' in js or
                f'%{{BKY_{key}}}' in js):
                blocklyMessageNames.append(key)
        
        # Check for BlocklyGames messages
        m = bg_re.search(msg)
        if m:
            key = m.group(1)
            # Check for quoted or dot notation usage
            if f'"{key}"' in js or f'.{key}' in js:
                blocklyGamesMessageNames.append(key)

    # Deduplicate and sort the lists
    blocklyMessageNames = sorted(list(set(blocklyMessageNames)))
    blocklyGamesMessageNames = sorted(list(set(blocklyGamesMessageNames)))
    
    print(f"🏷️ Found {len(blocklyMessageNames)} used Blockly messages.")
    print(f"🏷️ Found {len(blocklyGamesMessageNames)} used Blockly Games messages.")


def getMessages(lang: str) -> List[str]:
    """
    Reads all messages for a specific language.
    """
    msg_file = Path('server/html/generated/msg') / f'{lang}.js'
    if not msg_file.exists():
        # This warning is expected for languages other than 'en' if msg compilation hasn't happened yet.
        # But we only call this for 'en' in filterMessages, so it should exist.
        print(f"Warning: Language file not found: {msg_file}")
        return []

    return msg_file.read_text().splitlines()


def language(gameName: str, lang: str, generated_path: Path):
    """
    Generates the minimized JS message file for a specific language,
    containing only the messages identified as used.
    """
    global blocklyMessageNames, blocklyGamesMessageNames
    
    msgs = getMessages(lang)
    if not msgs:
        return # Skip if no messages found

    bMsgs = []
    bgMsgs = []
    
    blockly_re = re.compile(r'BlocklyMsg\["([^"]+)"\] = (.*);\s*')
    bg_re = re.compile(r'BlocklyGamesMsg\["([^"]+)"\] = (.*);\s*')
    
    for msg in msgs:
        # Process Blockly Messages
        m = blockly_re.search(msg)
        if m and m.group(1) in blocklyMessageNames:
            # Blockly message names are typically alphabetic, no need to quote keys.
            bMsgs.append(f'{m.group(1)}:{m.group(2)}')
        
        # Process Blockly Games Messages
        m = bg_re.search(msg)
        if m and m.group(1) in blocklyGamesMessageNames:
            # Blockly Games message names contain dots, quotes required for keys.
            bgMsgs.append(f'"{m.group(1)}":{m.group(2)}')

    # Create the language file directory
    msg_dir = generated_path / 'msg'
    msg_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = msg_dir / f'{lang}.js'
    
    # Write the minimized message objects
    with output_file.open('w') as f:
        f.write(WARNING)
        if bMsgs:
            f.write(f"var BlocklyMsg={{{','.join(bMsgs)}}}\n")
        if bgMsgs:
            f.write(f"var BlocklyGamesMsg={{{','.join(bgMsgs)}}}\n")
            
    print(f"  - Message file created: {lang}.js")


def generate_uncompressed(gameName: str, game_path: Path, generated_path: Path):
    """
    Uses Closure Builder to extract the dependency list and creates the uncompressed JS loader file.
    """
    print("✨ Extracting Dependencies (uncompressed.js)...")
    
    cmd = [
        'third-party/closurebuilder/closurebuilder.py',
        '--root=server/html/third-party/',
        '--root=server/html/generated/',
        '--root=server/html/src/',
        '--exclude=',
        f'--namespace={gameName.replace("/", ".").title()}'
    ]
    
    # Add source and generated directories from the game's path and its parent directories
    current_dir = Path(gameName)
    # Loop up the directory tree (e.g., from 'maze' to '.')
    while current_dir != Path('.'):
        subdir_generated = Path('server/html') / current_dir / 'generated/'
        if subdir_generated.is_dir():
            cmd.append(f'--root={subdir_generated}')
        subdir_src = Path('server/html') / current_dir / 'src/'
        if subdir_src.is_dir():
            cmd.append(f'--root={subdir_src}')
        
        # Move to the parent directory
        parent_dir = current_dir.parent
        if parent_dir == current_dir: # Break if at the root
            break
        current_dir = parent_dir
    
    try:
        # Run closurebuilder; output is a list of dependency files
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        files = proc.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        print(f"Error: Closure Builder failed (uncompressed): {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: closurebuilder.py not found. Check the path.")
        sys.exit(1)

    # Process file paths to be relative to the HTML root
    prefix = 'server/html/'
    # Handle the special case where 'pond/docs' needs to access files in 'server/html/' via '../'
    path_prefix = '../' if gameName == 'pond/docs' else ''
    srcs = []
    
    for file in files:
        file = file.strip()
        if file.startswith(prefix):
            file = file[len(prefix):]
        else:
            raise Exception(f'"{file}" is not in the expected "{prefix}" directory.')
        srcs.append(f'"{path_prefix}{file}"')
    
    output_file = generated_path / 'uncompressed.js'
    
    # Generate the JS loader script content
    script_content = f"""{WARNING}
window.CLOSURE_NO_DEPS = true;

(function() {{
    var srcs = [
        {',\n        '.join(srcs)}
    ];
    function loadScript() {{
        var src = srcs.shift();
        if (src) {{
            var script = document.createElement('script');
            script.src = src;
            script.type = 'text/javascript';
            script.onload = loadScript;
            document.head.appendChild(script);
        }}
    }}
    loadScript();
}})();
"""
    output_file.write_text(script_content)
    print(f'  - Found {len(srcs)} dependencies and created uncompressed.js.')


def generate_compressed(gameName: str, game_path: Path, generated_path: Path):
    """
    Uses Closure Compiler to compress the JS code into a single file.
    """
    print("🔥 Compressing JavaScript Code (compressed.js)...")
    
    # Define the main entry point
    entry_point = Path('server/html') / gameName / 'src/main'

    cmd = [
        'java',
        '-jar', 'build/third-party-downloads/closure-compiler.jar',
        '--generate_exports',
        '--compilation_level', 'ADVANCED_OPTIMIZATIONS',
        '--dependency_mode=PRUNE',
        # External definitions (externs) for global symbols not known to the compiler
        '--externs', 'externs/interpreter-externs.js',
        '--externs', 'externs/prettify-externs.js',
        '--externs', 'externs/soundJS-externs.js',
        '--externs', 'externs/storage-externs.js',
        '--externs', 'externs/svg-externs.js',
        '--language_out', 'ECMASCRIPT5',
        f'--entry_point={entry_point}',
        # Base and common files
        "--js='server/html/third-party/base.js'",
        "--js='server/html/third-party/blockly/**.js'",
        "--js='server/html/src/*.js'",
        '--warning_level', 'QUIET',
    ]
    
    # Add source files from the game's path and its parents
    current_dir = Path(gameName)
    while current_dir != Path('.'):
        cmd.append(f"--js='server/html/{current_dir}/src/*.js'")
        # Move to the parent directory
        parent_dir = current_dir.parent
        if parent_dir == current_dir:
            break
        current_dir = parent_dir
    
    try:
        # Run Closure Compiler
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        script = proc.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error: Closure Compiler failed (compressed): {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: closure-compiler.jar not found. Check the path.")
        sys.exit(1)

    # Strip out Apache 2.0 licenses from Google/MIT
    script = trim_licence(script)
    
    # Write the output file
    output_file = generated_path / 'compressed.js'
    output_file.write_text(WARNING + script)

    print(f'  - Compressed to {len(script) / 1024:.2f} KB.')


def trim_licence(code: str) -> str:
    """
    Strips out Google's and MIT's Apache 2.0 licences from the compiled code.

    Args:
      code: Large blob of compiled source code.

    Returns:
      Code with Google's and MIT's Apache licences trimmed.
    """
    # Regex pattern for the multi-line Apache 2.0 license header
    apache2_re = re.compile(
        r'/\*\s*\n'
        r'(Copyright \d+ (Google LLC|Massachusetts Institute of Technology))'
        r'( All rights reserved.\n)?'
        r' SPDX-License-Identifier: Apache-2.0\n'
        r'\*/',
        re.DOTALL
    )
    return apache2_re.sub('', code)


# The original readStdout function is no longer needed as subprocess.run(text=True) handles encoding.

if __name__ == '__main__':
    # Check for command line arguments
    if len(sys.argv) == 2:
        # Pass the game name to the main function
        main(sys.argv[1])
    else:
        print(f'Usage: {sys.argv[0]} <appname>')
        sys.exit(2)
