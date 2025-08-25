# backend/src/main.py - FIXED VERSION WITH CORRECTED ASYNC SYNTAX
# This version fixes the async/await syntax error and prevents infinite loops

import os
import sys
import logging
import time
import re
import json

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any

import httpx
from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import BaseModel

# Disable Flask's default request logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#6GSgvasgr$SSMGT'

# Enable CORS for all routes
CORS(app, origins="*")

# ElevenLabs configuration
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY', 'your-api-key-here')
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"

# Your ElevenLabs phone number ID
ELEVENLABS_PHONE_NUMBER_ID = "phnum_8301k3dyf6s8etgtzp4c60pct5s9"

# Store active calls and results (in production, use a database)
active_calls = {}
call_results = {}
conversation_data = {}
processed_calls = set()  # Track which calls we've already processed to avoid loops

# Pydantic models for request/response
class CallRequest(BaseModel):
    phone_number: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = "AI Assistant"
    call_purpose: Optional[str] = "Information gathering"
    questions: Optional[List[str]] = []
    voice_id: Optional[str] = "21m00Tcm4TlvDq8ikWAM"
    language: Optional[str] = "en"
    first_message: Optional[str] = None
    custom_prompt: Optional[str] = None

class AgentConfig(BaseModel):
    name: str
    prompt: str
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    language: str = "en"
    first_message: Optional[str] = None

class ElevenLabsClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }

    async def create_agent(self, config: AgentConfig) -> Dict:
        """Create a new agent with ElevenLabs"""
        url = f"{ELEVENLABS_BASE_URL}/convai/agents/create"
        
        payload = {
            "name": config.name,
            "conversation_config": {
                "agent": {
                    "prompt": {
                        "prompt": config.prompt
                    },
                    "first_message": config.first_message or f"Hello! I'm {config.name}.",
                    "language": config.language
                },
                "asr": {
                    "quality": "high"
                },
                "tts": {
                    "voice_id": config.voice_id
                },
                "llm": {
                    "model": "gpt-4"
                }
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self.headers)
            print(f"🔍 Agent Creation - Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Agent created: {result.get('agent_id', 'Unknown')}")
                return {"success": True, "agent_id": result.get("agent_id"), "data": result}
            else:
                error_text = response.text
                print(f"❌ Agent creation failed: {response.status_code} - {error_text}")
                return {"success": False, "error": f"Failed to create agent: {response.status_code} - {error_text}"}

    async def create_batch_call(self, agent_id: str, phone_number: str, call_name: str) -> Dict:
        """Create a batch call with ElevenLabs"""
        url = f"{ELEVENLABS_BASE_URL}/convai/batch-calling/submit"
        
        current_time = int(time.time())
        
        payload = {
            "call_name": call_name,
            "agent_id": agent_id,
            "agent_phone_number_id": ELEVENLABS_PHONE_NUMBER_ID,
            "scheduled_time_unix": current_time,
            "recipients": [
                {
                    "phone_number": phone_number
                }
            ]
        }
        
        print(f"🔍 Batch Call Payload: {json.dumps(payload, indent=2)}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self.headers)
            print(f"🔍 Batch Call - Status: {response.status_code}")
            print(f"🔍 Batch Call - Response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                batch_call_id = result.get("id")
                print(f"✅ Call initiated successfully: {batch_call_id}")
                return {"success": True, "batch_call_id": batch_call_id, "data": result}
            else:
                error_text = response.text
                print(f"❌ Batch call failed: {response.status_code} - {error_text}")
                return {"success": False, "error": f"Failed to create batch call: {response.status_code} - {error_text}"}

    async def get_batch_call_status(self, batch_call_id: str) -> Dict:
        """Get the status of a batch call"""
        url = f"{ELEVENLABS_BASE_URL}/convai/batch-calling/{batch_call_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                return {"success": True, "data": result}
            else:
                return {"success": False, "error": f"Failed to get call status: {response.status_code} - {response.text}"}

    async def get_conversations(self) -> Dict:
        """Get all conversations from ElevenLabs"""
        url = f"{ELEVENLABS_BASE_URL}/convai/conversations"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                return {"success": True, "conversations": result.get("conversations", [])}
            else:
                return {"success": False, "error": f"Failed to get conversations: {response.status_code} - {response.text}"}

    async def get_conversation_by_id(self, conversation_id: str) -> Dict:
        """Get a specific conversation by ID"""
        url = f"{ELEVENLABS_BASE_URL}/convai/conversations/{conversation_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                return {"success": True, "conversation": result}
            else:
                return {"success": False, "error": f"Failed to get conversation: {response.status_code} - {response.text}"}

# Initialize ElevenLabs client
elevenlabs_client = ElevenLabsClient(ELEVENLABS_API_KEY)

def extract_information_from_transcript(transcript: str, questions: List[str]) -> Dict:
    """Extract structured information from conversation transcript"""
    extracted_info = {}
    
    # Convert transcript to lowercase for easier matching
    transcript_lower = transcript.lower()
    
    for i, question in enumerate(questions):
        question_key = f"question_{i+1}"
        
        # Try to find answers based on common patterns
        answer = "Not answered"
        
        # Look for name patterns
        if "name" in question.lower():
            name_patterns = [
                r"my name is ([^.!?]+)",
                r"i'm ([^.!?]+)",
                r"i am ([^.!?]+)",
                r"call me ([^.!?]+)"
            ]
            for pattern in name_patterns:
                match = re.search(pattern, transcript_lower)
                if match:
                    answer = match.group(1).strip()
                    break
        
        # Look for email patterns
        elif "email" in question.lower():
            email_pattern = r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
            match = re.search(email_pattern, transcript)
            if match:
                answer = match.group(1)
        
        # Look for satisfaction/rating patterns
        elif any(word in question.lower() for word in ["satisfied", "satisfaction", "rating", "scale"]):
            rating_patterns = [
                r"(\d+)\s*out of\s*\d+",
                r"(\d+)\s*/\s*\d+",
                r"rate.*?(\d+)",
                r"(\d+)\s*(?:stars?|points?)"
            ]
            for pattern in rating_patterns:
                match = re.search(pattern, transcript_lower)
                if match:
                    answer = f"{match.group(1)}/10"
                    break
        
        # Look for medication patterns (for medical protocols)
        elif any(word in question.lower() for word in ["medication", "medicine", "lisinopril", "losartan"]):
            if any(word in transcript_lower for word in ["yes", "taking", "keep up", "continue"]):
                answer = "Yes, taking as prescribed"
            elif any(word in transcript_lower for word in ["no", "stopped", "not taking"]):
                answer = "No, not taking medication"
        
        # Look for symptoms patterns
        elif "symptom" in question.lower():
            if any(word in transcript_lower for word in ["headache", "dizziness", "swelling"]):
                symptoms = []
                if "headache" in transcript_lower:
                    symptoms.append("headaches")
                if "dizziness" in transcript_lower or "dizzy" in transcript_lower:
                    symptoms.append("dizziness")
                if "swelling" in transcript_lower or "swollen" in transcript_lower:
                    symptoms.append("swelling")
                answer = ", ".join(symptoms) if symptoms else "No specific symptoms mentioned"
            else:
                answer = "No symptoms mentioned"
        
        # Generic answer extraction (look for responses after question-like patterns)
        if answer == "Not answered":
            # Try to find any response that might be related to the question
            question_words = question.lower().split()
            for word in question_words:
                if len(word) > 3:  # Only look for meaningful words
                    pattern = rf"{word}.*?([^.!?]+)"
                    match = re.search(pattern, transcript_lower)
                    if match:
                        potential_answer = match.group(1).strip()
                        if len(potential_answer) > 5:  # Only use if it's a substantial answer
                            answer = potential_answer[:100]  # Limit length
                            break
        
        extracted_info[question_key] = {
            "question": question,
            "answer": answer
        }
    
    return extracted_info

async def find_conversation_for_call(batch_call_id: str, agent_id: str, max_attempts: int = 5) -> Dict:
    """Find conversation for a specific call with multiple attempts and fallback strategies"""
    
    # Check if we've already processed this call
    if batch_call_id in processed_calls:
        print(f"⚠️  Call {batch_call_id} already processed, skipping")
        return {"success": False, "message": "Call already processed"}
    
    for attempt in range(1, max_attempts + 1):
        print(f"🔍 Attempt {attempt}/{max_attempts} to find conversation for call {batch_call_id}")
        
        # Get all conversations
        conversations_result = await elevenlabs_client.get_conversations()
        
        if not conversations_result["success"]:
            print(f"❌ Failed to get conversations: {conversations_result['error']}")
            continue
        
        conversations = conversations_result["conversations"]
        print(f"📋 Found {len(conversations)} total conversations")
        
        # Strategy 1: Look for exact batch_call_id match
        for conv in conversations:
            if conv.get("batch_call_id") == batch_call_id:
                print(f"✅ Found conversation by batch_call_id: {conv.get('conversation_id')}")
                return {"success": True, "conversation": conv}
        
        # Strategy 2: Look for agent_id match (fallback)
        for conv in conversations:
            if conv.get("agent_id") == agent_id:
                print(f"✅ Found conversation by agent_id: {conv.get('conversation_id')}")
                return {"success": True, "conversation": conv}
        
        # Strategy 3: Look for recent conversations (within last 10 minutes)
        current_time = int(time.time())
        for conv in conversations:
            conv_time = conv.get("start_time_unix", 0)
            if current_time - conv_time < 600:  # 10 minutes
                print(f"✅ Found recent conversation: {conv.get('conversation_id')}")
                return {"success": True, "conversation": conv}
        
        # Wait before next attempt
        if attempt < max_attempts:
            print(f"⏳ Waiting 10 seconds before attempt {attempt + 1}...")
            await asyncio.sleep(10)
    
    print(f"❌ No conversation found for call {batch_call_id} after {max_attempts} attempts")
    return {
        "success": False, 
        "message": f"No conversation found after {max_attempts} attempts",
        "debug_info": {
            "batch_call_id": batch_call_id,
            "agent_id": agent_id,
            "total_conversations": len(conversations) if 'conversations' in locals() else 0,
            "attempts": max_attempts
        }
    }

def generate_agent_prompt(agent_name: str, call_purpose: str, questions: List[str], custom_prompt: str = None) -> str:
    """Generate a comprehensive prompt for the AI agent"""
    
    if custom_prompt:
        return custom_prompt
    
    questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
    
    prompt = f"""You are {agent_name}, a professional and friendly AI assistant conducting a {call_purpose}.

Your primary objectives:
1. Be polite, professional, and conversational
2. Ask the following questions in a natural way:

{questions_text}

Guidelines:
- Introduce yourself clearly at the beginning
- Ask questions one at a time and wait for responses
- Be patient and understanding if the person needs clarification
- Keep the conversation focused but natural
- Thank the person for their time at the end
- If someone seems uncomfortable, be respectful and offer to end the call

Remember: You are representing a professional organization, so maintain a courteous and helpful tone throughout the conversation."""

    return prompt

# Custom 404 handler to suppress Socket.IO logs
@app.errorhandler(404)
def handle_404(e):
    # Silently handle Socket.IO requests
    if 'socket.io' in request.path:
        return '', 404
    return jsonify({"error": "Not found"}), 404

@app.route('/')
def root():
    return jsonify({"message": "CEX Protocol AI Backend API"})

@app.route('/api/test')
def test_endpoint():
    print("✅ Backend test endpoint called successfully")
    api_key_configured = "Yes" if ELEVENLABS_API_KEY and ELEVENLABS_API_KEY != 'your-api-key-here' else "No"
    phone_number_configured = "Yes" if ELEVENLABS_PHONE_NUMBER_ID else "No"
    
    return jsonify({
        "message": "Backend is working!",
        "elevenlabs_api_configured": api_key_configured,
        "phone_number_configured": phone_number_configured,
        "phone_number_id": ELEVENLABS_PHONE_NUMBER_ID
    })

@app.route('/api/test-agent-creation', methods=['POST'])
def test_agent_creation():
    try:
        data = request.get_json()
        agent_name = data.get('agentName', 'Test AI Assistant')
        call_purpose = data.get('callPurpose', 'Test call')
        questions = data.get('questions', ['What is your name?'])
        voice_id = data.get('voiceId', '21m00Tcm4TlvDq8ikWAM')
        
        print(f"🧪 Testing agent creation: {agent_name}")
        
        # Generate prompt
        prompt = generate_agent_prompt(agent_name, call_purpose, questions)
        
        # Create agent config
        agent_config = AgentConfig(
            name=agent_name,
            prompt=prompt,
            voice_id=voice_id
        )
        
        # Create agent
        result = asyncio.run(elevenlabs_client.create_agent(agent_config))
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": "Test agent created successfully",
                "agent_id": result["agent_id"]
            })
        else:
            return jsonify({
                "success": False,
                "message": "Failed to create test agent",
                "error": result["error"]
            }), 500
            
    except Exception as e:
        print(f"❌ Error in test agent creation: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error testing agent creation",
            "error": str(e)
        }), 500

@app.route('/api/make-call', methods=['POST'])
def make_call():
    try:
        data = request.get_json()
        phone_number = data.get('phoneNumber')
        agent_name = data.get('agentName', 'AI Assistant')
        call_purpose = data.get('callPurpose', 'Information gathering')
        questions = data.get('questions', [])
        voice_id = data.get('voiceId', '21m00Tcm4TlvDq8ikWAM')
        first_message = data.get('firstMessage', '')
        custom_prompt = data.get('customPrompt', '')
        
        print(f"📞 Make call request for: {phone_number}")
        
        if not phone_number:
            return jsonify({"success": False, "error": "Phone number is required"}), 400
        
        # Create new agent for this call
        print("🤖 Creating new agent for call...")
        prompt = generate_agent_prompt(agent_name, call_purpose, questions, custom_prompt)
        
        agent_config = AgentConfig(
            name=agent_name,
            prompt=prompt,
            voice_id=voice_id,
            first_message=first_message
        )
        
        agent_result = asyncio.run(elevenlabs_client.create_agent(agent_config))
        
        if not agent_result["success"]:
            return jsonify({
                "success": False,
                "error": agent_result["error"],
                "message": "Failed to create agent"
            }), 500
        
        agent_id = agent_result["agent_id"]
        
        # Create batch call
        print(f"📞 Initiating call to {phone_number} with agent {agent_id}")
        call_name = f"AI Call to {phone_number}"
        
        call_result = asyncio.run(elevenlabs_client.create_batch_call(agent_id, phone_number, call_name))
        
        if not call_result["success"]:
            return jsonify({
                "success": False,
                "error": call_result["error"],
                "message": "Failed to initiate call"
            }), 500
        
        batch_call_id = call_result["batch_call_id"]
        
        # Store call information
        active_calls[batch_call_id] = {
            "phone_number": phone_number,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "purpose": call_purpose,
            "questions": questions,
            "status": "initiated",
            "start_time": datetime.now().isoformat(),
            "conversation_processed": False
        }
        
        return jsonify({
            "success": True,
            "message": "Call initiated successfully",
            "batch_call_id": batch_call_id,
            "agent_id": agent_id
        })
        
    except Exception as e:
        print(f"❌ Error making call: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to initiate call"
        }), 500

@app.route('/api/call-status/<batch_call_id>')
def get_call_status(batch_call_id):
    try:
        print(f"📋 Getting status for call: {batch_call_id}")
        
        # Get status from ElevenLabs
        status_result = asyncio.run(elevenlabs_client.get_batch_call_status(batch_call_id))
        
        if not status_result["success"]:
            return jsonify({
                "success": False,
                "error": status_result["error"]
            }), 500
        
        call_data = status_result["data"]
        status = call_data.get("status", "unknown")
        
        # Update local storage
        if batch_call_id in active_calls:
            active_calls[batch_call_id]["status"] = status
            active_calls[batch_call_id]["last_updated"] = datetime.now().isoformat()
        
        # Prepare response
        call_info = {
            "batch_call_id": batch_call_id,
            "status": status,
            "call_data": call_data
        }
        
        # Add conversation results if available
        if batch_call_id in call_results:
            call_info["conversation_results"] = call_results[batch_call_id]
        
        return jsonify({
            "success": True,
            "call_info": call_info
        })
        
    except Exception as e:
        print(f"❌ Error getting call status: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/process-conversation/<batch_call_id>', methods=['POST'])
def process_conversation(batch_call_id):
    """Manually process conversation for a specific call"""
    try:
        print(f"🔄 Manual conversation processing for call: {batch_call_id}")
        
        if batch_call_id not in active_calls:
            return jsonify({
                "success": False,
                "message": "Call not found in active calls"
            }), 404
        
        call_info = active_calls[batch_call_id]
        agent_id = call_info["agent_id"]
        questions = call_info.get("questions", [])
        
        # Find conversation - FIXED: Use asyncio.run() to handle async function
        conversation_result = asyncio.run(find_conversation_for_call(batch_call_id, agent_id))
        
        if not conversation_result["success"]:
            return jsonify({
                "success": False,
                "message": conversation_result["message"],
                "debug_info": conversation_result.get("debug_info")
            }), 404
        
        conversation = conversation_result["conversation"]
        conversation_id = conversation.get("conversation_id")
        
        # Get full conversation details - FIXED: Use asyncio.run() to handle async function
        conv_details_result = asyncio.run(elevenlabs_client.get_conversation_by_id(conversation_id))
        
        if conv_details_result["success"]:
            conv_details = conv_details_result["conversation"]
            transcript = conv_details.get("transcript", "No transcript available")
        else:
            transcript = "Could not retrieve transcript"
        
        # Extract information
        extracted_info = extract_information_from_transcript(transcript, questions)
        
        # Store results
        results = {
            "conversation_id": conversation_id,
            "transcript": transcript,
            "extracted_info": extracted_info,
            "processed_at": datetime.now().isoformat()
        }
        
        call_results[batch_call_id] = results
        active_calls[batch_call_id]["conversation_processed"] = True
        processed_calls.add(batch_call_id)  # Mark as processed
        
        print(f"✅ Conversation processed successfully for call {batch_call_id}")
        
        return jsonify({
            "success": True,
            "message": "Conversation processed successfully",
            "results": results
        })
        
    except Exception as e:
        print(f"❌ Error processing conversation: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to process conversation"
        }), 500

@app.route('/api/debug-conversations')
def debug_conversations():
    """Get all conversations for debugging purposes"""
    try:
        print("🔍 Fetching all conversations for debugging...")
        
        conversations_result = asyncio.run(elevenlabs_client.get_conversations())
        
        if conversations_result["success"]:
            conversations = conversations_result["conversations"]
            
            # Format for debugging
            debug_info = {
                "total_conversations": len(conversations),
                "conversations": []
            }
            
            for conv in conversations:
                debug_info["conversations"].append({
                    "conversation_id": conv.get("conversation_id"),
                    "agent_id": conv.get("agent_id"),
                    "batch_call_id": conv.get("batch_call_id"),
                    "start_time": conv.get("start_time_unix"),
                    "status": conv.get("status")
                })
            
            return jsonify({
                "success": True,
                "conversations": debug_info
            })
        else:
            return jsonify({
                "success": False,
                "error": conversations_result["error"]
            }), 500
            
    except Exception as e:
        print(f"❌ Error getting debug conversations: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/active-calls')
def get_active_calls():
    """Get all active calls"""
    return jsonify({
        "success": True,
        "active_calls": active_calls
    })

@app.route('/api/call-results/<batch_call_id>')
def get_call_results(batch_call_id):
    """Get conversation results for a specific call"""
    if batch_call_id in call_results:
        return jsonify({
            "success": True,
            "results": call_results[batch_call_id]
        })
    else:
        return jsonify({
            "success": False,
            "message": "No results found for this call"
        }), 404

if __name__ == '__main__':
    print("🚀 Starting CEX Protocol AI Backend on http://0.0.0.0:5001")
    api_key_status = "Yes" if ELEVENLABS_API_KEY and ELEVENLABS_API_KEY != 'your-api-key-here' else "No"
    print(f"🔑 ElevenLabs API Key configured: {api_key_status}")
    print("✨ Server ready! Logs will show important events only.")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
