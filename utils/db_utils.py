"""
Utility script to query and analyze voice assistant conversations
Usage: python db_utils.py [command] [arguments]
"""

import argparse
from db_driver import DatabaseDriver
from datetime import datetime
import json


def print_conversation(conv):
    """Pretty print a conversation entry"""
    timestamp = datetime.fromisoformat(conv.timestamp).strftime('%Y-%m-%d %H:%M:%S')
    speaker_label = "🤖 ASSISTANT" if conv.speaker == "assistant" else "👤 USER"
    print(f"\n[{timestamp}] {speaker_label}")
    print(f"  {conv.message}")
    if conv.metadata:
        print(f"  Metadata: {conv.metadata}")


def print_tool_call(tool):
    """Pretty print a tool call"""
    timestamp = datetime.fromisoformat(tool.timestamp).strftime('%Y-%m-%d %H:%M:%S')
    status = "✓" if tool.success else "✗"
    print(f"\n[{timestamp}] {status} TOOL: {tool.tool_name}")
    print(f"  Parameters: {json.dumps(tool.parameters, indent=4)}")
    if tool.result:
        print(f"  Result: {tool.result}")


def view_session(db: DatabaseDriver, session_id: str):
    """View all conversations in a session"""
    conversations = db.get_conversation_history(session_id)
    
    if not conversations:
        print(f"No conversations found for session: {session_id}")
        return
    
    print(f"\n{'='*60}")
    print(f"SESSION: {session_id}")
    print(f"Total messages: {len(conversations)}")
    print(f"{'='*60}")
    
    for conv in conversations:
        print_conversation(conv)
        
        # Check for tool calls
        tool_calls = db.get_tool_calls_for_conversation(conv.id)
        for tool in tool_calls:
            print_tool_call(tool)
    
    print(f"\n{'='*60}\n")


def list_sessions(db: DatabaseDriver):
    """List all sessions"""
    sessions = db.get_active_sessions()
    
    print(f"\n{'='*60}")
    print("ALL SESSIONS")
    print(f"{'='*60}")
    
    if not sessions:
        print("No sessions found")
        return
    
    for session in sessions:
        count = db.get_conversation_count(session['session_id'])
        start = datetime.fromisoformat(session['start_time']).strftime('%Y-%m-%d %H:%M:%S')
        end = session['end_time']
        status = "ACTIVE" if not end else "ENDED"
        
        print(f"\nSession ID: {session['session_id']}")
        print(f"  Participant: {session['participant_id']}")
        print(f"  Status: {status}")
        print(f"  Start: {start}")
        if end:
            print(f"  End: {datetime.fromisoformat(end).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Messages: {count}")


def recent_conversations(db: DatabaseDriver, participant_id: str, limit: int = 10):
    """Show recent conversations for a participant"""
    conversations = db.get_recent_conversations(participant_id, limit)
    
    if not conversations:
        print(f"No conversations found for participant: {participant_id}")
        return
    
    print(f"\n{'='*60}")
    print(f"RECENT CONVERSATIONS - {participant_id}")
    print(f"{'='*60}")
    
    for conv in conversations:
        print_conversation(conv)


def tool_stats(db: DatabaseDriver, session_id: str = None):
    """Show tool usage statistics"""
    stats = db.get_tool_usage_stats(session_id)
    
    scope = f"Session: {session_id}" if session_id else "All Sessions"
    
    print(f"\n{'='*60}")
    print(f"TOOL USAGE STATISTICS - {scope}")
    print(f"{'='*60}\n")
    
    if not stats:
        print("No tool calls recorded")
        return
    
    total = sum(stats.values())
    print(f"Total tool calls: {total}\n")
    
    for tool_name, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total) * 100
        bar = "█" * int(percentage / 2)
        print(f"{tool_name:20} {bar} {count:3} ({percentage:.1f}%)")


def delete_session_data(db: DatabaseDriver, session_id: str):
    """Delete all data for a session"""
    confirm = input(f"Are you sure you want to delete session '{session_id}'? (yes/no): ")
    
    if confirm.lower() == 'yes':
        db.delete_session_data(session_id)
        print(f"Session '{session_id}' deleted successfully")
    else:
        print("Deletion cancelled")


def export_session(db: DatabaseDriver, session_id: str, output_file: str):
    """Export session to JSON file"""
    conversations = db.get_conversation_history(session_id)
    
    if not conversations:
        print(f"No conversations found for session: {session_id}")
        return
    
    export_data = {
        "session_id": session_id,
        "export_date": datetime.utcnow().isoformat(),
        "conversations": []
    }
    
    for conv in conversations:
        conv_data = {
            "id": conv.id,
            "speaker": conv.speaker,
            "message": conv.message,
            "timestamp": conv.timestamp,
            "metadata": conv.metadata
        }
        
        # Add tool calls if any
        tool_calls = db.get_tool_calls_for_conversation(conv.id)
        if tool_calls:
            conv_data["tool_calls"] = [
                {
                    "tool_name": t.tool_name,
                    "parameters": t.parameters,
                    "result": t.result,
                    "timestamp": t.timestamp,
                    "success": t.success
                }
                for t in tool_calls
            ]
        
        export_data["conversations"].append(conv_data)
    
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"Session exported to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Voice Assistant Database Utilities")
    parser.add_argument('command', choices=[
        'list', 'view', 'recent', 'stats', 'delete', 'export'
    ], help="Command to execute")
    parser.add_argument('--session', '-s', help="Session ID")
    parser.add_argument('--participant', '-p', help="Participant ID")
    parser.add_argument('--limit', '-l', type=int, default=10, help="Limit for results")
    parser.add_argument('--output', '-o', help="Output file for export")
    parser.add_argument('--db', default="voice_assistant.sqlite", help="Database path")
    
    args = parser.parse_args()
    
    db = DatabaseDriver(args.db)
    
    if args.command == 'list':
        list_sessions(db)
    
    elif args.command == 'view':
        if not args.session:
            print("Error: --session is required for 'view' command")
            return
        view_session(db, args.session)
    
    elif args.command == 'recent':
        if not args.participant:
            print("Error: --participant is required for 'recent' command")
            return
        recent_conversations(db, args.participant, args.limit)
    
    elif args.command == 'stats':
        tool_stats(db, args.session)
    
    elif args.command == 'delete':
        if not args.session:
            print("Error: --session is required for 'delete' command")
            return
        delete_session_data(db, args.session)
    
    elif args.command == 'export':
        if not args.session or not args.output:
            print("Error: --session and --output are required for 'export' command")
            return
        export_session(db, args.session, args.output)


if __name__ == "__main__":
    main()