#!/usr/bin/env bash
# ==============================================================================
# CYRUS Unified Controller CLI (Local macOS Management)
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

COMMAND="${1:-status}"
shift || true

echo "=================================================="
echo " CYRUS Local Controller • Personal AI Intelligence"
echo "=================================================="

case "$COMMAND" in
    voice)
        MESSAGE="$*"
        if [ -z "$MESSAGE" ]; then
            MESSAGE="Hey CYRUS, what is our system status?"
        fi
        echo "Testing Spoken Voice Turn: \"$MESSAGE\""
        python3 -c "
import asyncio, sys
sys.path.insert(0, '$PROJECT_ROOT')
from backend.app.voice.voice_pipeline import voice_pipeline

async def run():
    msg = '''$MESSAGE'''
    res = await voice_pipeline.execute_voice_turn(raw_transcript=msg, voice='Daniel', speak_on_mac=True)
    print(f'Detected Language: {res[\"detected_language\"]}')
    print(f'Wake Word Detected: {res[\"wake_word_triggered\"]}')
    print(f'CYRUS Spoken English: {res[\"speech_payload\"][\"text\"]}')
    print(f'Voice Used: {res[\"speech_payload\"][\"voice\"]} ({res[\"speech_payload\"][\"rate_wpm\"]} wpm)')
    if res.get('backend_spoken'):
        print('✓ Audio played via macOS local speaker.')

asyncio.run(run())
"
        ;;
    chat)
        MESSAGE="$*"
        if [ -n "$MESSAGE" ]; then
            python3 -c "
import asyncio, sys
sys.path.insert(0, '$PROJECT_ROOT')
from backend.app.core.orchestrator import cyrus_core

async def run():
    msg = '''$MESSAGE'''
    res = await cyrus_core.process_message(msg)
    print(f'Input Language: {res[\"detected_language\"]}')
    print(f'CYRUS: {res[\"response\"]}')

asyncio.run(run())
"
        else
            echo "Entering Interactive Terminal Chat with CYRUS (Type 'exit' to quit):"
            python3 -c "
import asyncio, sys
sys.path.insert(0, '$PROJECT_ROOT')
from backend.app.core.orchestrator import cyrus_core

async def interactive():
    sess = None
    while True:
        try:
            user_input = input('\nSaksham > ').strip()
            if not user_input or user_input.lower() in ['exit', 'quit', 'q']:
                print('CYRUS: Session closed. Goodbye, Saksham.')
                break
            res = await cyrus_core.process_message(user_input, session_id=sess)
            sess = res['session_id']
            print(f'CYRUS [{res[\"detected_language\"]} -> English]: {res[\"response\"]}')
        except (KeyboardInterrupt, EOFError):
            print('\nCYRUS: Session closed.')
            break

asyncio.run(interactive())
"
        fi
        ;;
    test)
        echo "Running CYRUS Architectural Test Suite..."
        python3 backend/tests/run_tests.py
        ;;
    status)
        echo "Checking CYRUS Local Status..."
        python3 -c "
import asyncio, sys
sys.path.insert(0, '$PROJECT_ROOT')
from backend.app.database import check_db_health
from backend.app.lifecycle.process_manager import process_manager
from backend.app.core.llm_client import llm_client
from backend.app.voice.voice_config import voice_settings

async def main():
    db = await check_db_health()
    procs = await process_manager.list_registered_processes()
    ollama = llm_client.check_connection()
    print(f'Database: {\"HEALTHY (WAL)\" if db.get(\"healthy\") else \"OFFLINE\"}')
    print(f'Lifecycle State: {process_manager.current_state.value}')
    print(f'Active Tracked Processes: {len(procs)}')
    print(f'Ollama Local Daemon: {\"CONNECTED (\" + str(len(ollama.get(\"available_models\", []))) + \" models)\" if ollama.get(\"connected\") else \"OFFLINE (Using deterministic-core baseline)\"}')
    print(f'Voice Engine: Local STT + TTS (Default Voice: {voice_settings.TTS_DEFAULT_VOICE})')

asyncio.run(main())
"
        ;;
    pause)
        echo "Pausing CYRUS task queue..."
        python3 -c "
import asyncio, sys
sys.path.insert(0, '$PROJECT_ROOT')
from backend.app.lifecycle.process_manager import process_manager
res = asyncio.run(process_manager.pause_system())
print(res['message'])
"
        ;;
    resume)
        echo "Resuming CYRUS operations..."
        python3 -c "
import asyncio, sys
sys.path.insert(0, '$PROJECT_ROOT')
from backend.app.lifecycle.process_manager import process_manager
res = asyncio.run(process_manager.resume_system())
print(res['message'])
"
        ;;
    exam)
        echo "Activating EXAM MODE (0% background footprint)..."
        python3 -c "
import asyncio, sys
sys.path.insert(0, '$PROJECT_ROOT')
from backend.app.lifecycle.process_manager import process_manager
res = asyncio.run(process_manager.enter_exam_mode())
print(res['message'])
"
        ;;
    help|*)
        echo "Usage: ./scripts/cyrus_ctl.sh [command]"
        echo ""
        echo "Commands:"
        echo "  voice [msg] - Test voice recognition and spoken English synthesis"
        echo "  chat [msg]  - Send a message to CYRUS or start interactive terminal chat"
        echo "  test        - Execute backend unit test suite (39 tests)"
        echo "  status      - Inspect local SQLite database, Ollama, voice, and processes"
        echo "  pause       - Pause active task queues"
        echo "  resume      - Resume active task queues"
        echo "  exam        - Enter Exam Mode (0% background CPU/RAM)"
        ;;
esac
