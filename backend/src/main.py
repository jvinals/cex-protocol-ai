# backend/src/main.py - FIXED VERSION WITHOUT INFINITE LOOPS
# This version prevents endless loops and handles conversation fetching properly

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
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$SSWGT'

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
    voice_id: Optional[str] = None

class AgentConfig(BaseModel):
    name: str
    prompt: str
    voice_id: str
    language: str = "en"
    first_message: Optional[str] = None

class ElevenLabsClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
    
    async def create_agent(self, config: AgentConfig) -> Dict[str, Any]:
        """Create a conversational AI agent"""
        async with httpx.AsyncClient() as client:
            payload = {
                "conversation_config": {
                    "agent": {
                        "prompt": {
                            "prompt": config.prompt
                        },
                        "first_message": config.first_message or f"Hello! I'm {config.name}. How can I help you today?",
                        "language": config.language
                    },
                    "tts": {
                        "voice_id": config.voice_id
                    },
                    "asr": {
                        "quality": "high"
                    }
                },
                "name": config.name
            }
            
            response = await client.post(
                f"{ELEVENLABS_BASE_URL}/convai/agents/create",
                headers=self.headers,
                json=payload
            )
            
            print(f"🔍 Agent Creation - Status: {response.status_code}")
            if response.status_code != 200:
                print(f"🔍 Agent Creation - Error: {response.text}")
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to create agent: {response.status_code} - {response.text}")
    
    async def create_batch_call(self, phone_number: str, agent_id: str) -> Dict[str, Any]:
        """Create a batch call"""
        async with httpx.AsyncClient() as client:
            current_time = int(time.time())
            
            payload = {
                "call_name": f"AI Call to {phone_number}",
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
            
            response = await client.post(
                f"{ELEVENLABS_BASE_URL}/convai/batch-calling/submit",
                headers=self.headers,
                json=payload
            )
            
            print(f"🔍 Batch Call - Status: {response.status_code}")
            print(f"🔍 Batch Call - Response: {response.text}")
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to create batch call: {response.status_code} - {response.text}")
    
    async def get_batch_calls(self) -> Dict[str, Any]:
        """Get all batch calls"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ELEVENLABS_BASE_URL}/convai/batch-calling",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to get batch calls: {response.status_code} - {response.text}")
    
    async def get_batch_call_details(self, batch_call_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific batch call"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ELEVENLABS_BASE_URL}/convai/batch-calling/{batch_call_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to get batch call details: {response.status_code} - {response.text}")
    
    async def get_conversations(self) -> Dict[str, Any]:
        """Get all conversations"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ELEVENLABS_BASE_URL}/convai/conversations",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to get conversations: {response.status_code} - {response.text}")
    
    async def get_conversation_details(self, conversation_id: str) -> Dict[str, Any]:
        """Get detailed conversation transcript"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ELEVENLABS_BASE_URL}/convai/conversations/{conversation_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to get conversation details: {response.status_code} - {response.text}")

# Initialize ElevenLabs client
elevenlabs_client = ElevenLabsClient(ELEVENLABS_API_KEY)

def extract_information_from_transcript(transcript: str, questions: List[str]) -> Dict[str, Any]:
    """Extract structured information from conversation transcript"""
    extracted_info = {}
    
    # Simple extraction logic - you can enhance this with AI/NLP
    transcript_lower = transcript.lower()
    
    for i, question in enumerate(questions):
        question_key = f"question_{i+1}"
        extracted_info[question_key] = {
            "question": question,
            "answer": "Not answered or unclear"
        }
        
        # Try to find answers based on question keywords
        if "name" in question.lower():
            # Look for name patterns
            name_patterns = [
                r"my name is ([a-zA-Z\s]+)",
                r"i'm ([a-zA-Z\s]+)",
                r"this is ([a-zA-Z\s]+)",
                r"call me ([a-zA-Z\s]+)"
            ]
            for pattern in name_patterns:
                match = re.search(pattern, transcript_lower)
                if match:
                    extracted_info[question_key]["answer"] = match.group(1).strip().title()
                    break
        
        elif "email" in question.lower():
            # Look for email patterns
            email_pattern = r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
            match = re.search(email_pattern, transcript_lower)
            if match:
                extracted_info[question_key]["answer"] = match.group(1)
        
        elif "satisfied" in question.lower() or "rating" in question.lower() or "scale" in question.lower():
            # Look for satisfaction ratings
            rating_patterns = [
                r"(\d+)\s*out of\s*(\d+)",
                r"(\d+)\s*/\s*(\d+)",
                r"rate.*?(\d+)",
                r"(\d+)\s*stars?",
                r"scale.*?(\d+)",
                r"(\d+)\s*to\s*(\d+)"
            ]
            for pattern in rating_patterns:
                match = re.search(pattern, transcript_lower)
                if match:
                    if len(match.groups()) > 1:
                        extracted_info[question_key]["answer"] = f"{match.group(1)}/{match.group(2)}"
                    else:
                        extracted_info[question_key]["answer"] = f"{match.group(1)}/10"
                    break
        
        elif "medication" in question.lower() or "medicine" in question.lower() or "lisinopril" in question.lower() or "losartan" in question.lower():
            # Look for medication mentions
            medication_patterns = [
                r"taking ([a-zA-Z\s]+)",
                r"prescribed ([a-zA-Z\s]+)",
                r"medication.*?([a-zA-Z\s]+)",
                r"medicine.*?([a-zA-Z\s]+)",
                r"lisinopril",
                r"losartan",
                r"yes.*taking",
                r"no.*taking"
            ]
            for pattern in medication_patterns:
                match = re.search(pattern, transcript_lower)
                if match:
                    if match.groups():
                        extracted_info[question_key]["answer"] = match.group(1).strip().title()
                    else:
                        extracted_info[question_key]["answer"] = match.group(0).strip().title()
                    break
    
    return extracted_info

@app.route('/')
def home():
    return {"message": "CEX Protocol AI Backend API"}

@app.route('/api/test', methods=['GET'])
def test():
    """Test endpoint to verify routing is working"""
    print("✅ Backend test endpoint called successfully")
    return jsonify({'message': 'Phone calls API is working!'})

@app.route('/api/create-agent', methods=['POST'])
def create_agent():
    """Create a new conversational AI agent"""
    try:
        data = request.get_json()
        print(f"📝 Creating agent: {data.get('name', 'AI Assistant')}")
        
        config = AgentConfig(
            name=data.get('name', 'AI Assistant'),
            prompt=data.get('prompt', 'You are a helpful AI assistant.'),
            voice_id=data.get('voice_id', '21m00Tcm4TlvDq8ikWAM'),
            language=data.get('language', 'en'),
            first_message=data.get('first_message')
        )
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(elevenlabs_client.create_agent(config))
        loop.close()
        
        print(f"✅ Agent created successfully: {result.get('agent_id')}")
        
        return jsonify({
            "success": True,
            "agent_id": result.get("agent_id"),
            "message": "Agent created successfully"
        })
        
    except Exception as e:
        print(f"❌ Error creating agent: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to create agent"
        }), 500

@app.route('/api/make-call', methods=['POST'])
def make_call():
    """Initiate an AI phone call"""
    try:
        data = request.get_json()
        print(f"📞 Make call request for: {data.get('phoneNumber')}")
        
        phone_number = data.get('phoneNumber')
        agent_id = data.get('agentId')
        questions = data.get('questions', [])
        
        if not phone_number:
            return jsonify({
                'success': False,
                'error': 'phoneNumber is required'
            }), 400
        
        # Create agent if needed
        if not agent_id or agent_id == "create_new":
            print("🤖 Creating new agent for call...")
            
            # Build custom prompt based on your current template structure
            custom_prompt = data.get('customPrompt', '')
            if not custom_prompt:
                custom_prompt = f"""You are a professional AI assistant calling on behalf of Dr. Vinals. Be polite, professional, and empathetic.

Your goal is to have a natural conversation and gather the following information:
{chr(10).join(f"- {q}" for q in questions) if questions else "- General information as appropriate"}

Guidelines:
- Be polite and professional
- Introduce yourself and explain the purpose of the call
- Ask questions naturally in conversation
- Listen to responses and ask follow-up questions if needed
- Thank the person for their time at the end
- Keep the call concise but thorough

Start the conversation with a friendly greeting and introduction."""
            
            agent_config = AgentConfig(
                name=data.get('agentName', 'AI Assistant'),
                prompt=custom_prompt,
                voice_id=data.get('voiceId', '21m00Tcm4TlvDq8ikWAM'),
                language="en",
                first_message=data.get('firstMessage') or f"Hello! This is {data.get('agentName', 'an AI assistant')}. I'm calling regarding {data.get('callPurpose', 'a brief survey')}. Do you have a few minutes to chat?"
            )
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            agent_result = loop.run_until_complete(elevenlabs_client.create_agent(agent_config))
            agent_id = agent_result["agent_id"]
            loop.close()
            print(f"✅ Agent created: {agent_id}")
        
        # Make the call
        print(f"📞 Initiating call to {phone_number} with agent {agent_id}")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        call_result = loop.run_until_complete(
            elevenlabs_client.create_batch_call(phone_number, agent_id)
        )
        loop.close()
        
        batch_call_id = call_result.get("id")
        
        # Store call information
        active_calls[batch_call_id] = {
            "phone_number": phone_number,
            "agent_id": agent_id,
            "status": "initiated",
            "start_time": datetime.now().isoformat(),
            "purpose": data.get('callPurpose'),
            "questions": questions,
            "batch_call_data": call_result,
            "agent_name": data.get('agentName', 'AI Assistant'),
            "conversation_processed": False  # Track if we've processed the conversation
        }
        
        print(f"✅ Call initiated successfully: {batch_call_id}")
        
        return jsonify({
            'success': True,
            'batch_call_id': batch_call_id,
            'agent_id': agent_id,
            'status': 'initiated',
            'message': 'Call initiated successfully! The AI will call the number shortly.',
            'call_details': call_result
        })
        
    except Exception as e:
        print(f"❌ Error making call: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to initiate call'
        }), 500

@app.route('/api/test-agent-creation', methods=['POST'])
def test_agent_creation():
    """Test agent creation without making a call"""
    try:
        data = request.get_json()
        print(f"🧪 Testing agent creation: {data.get('agentName', 'Test Agent')}")
        
        agent_config = AgentConfig(
            name=data.get('agentName', 'Test AI Assistant'),
            prompt=f"""You are a test AI assistant for {data.get('callPurpose', 'testing purposes')}.

Your goal would be to have a natural conversation and gather information about:
{chr(10).join(f"- {q}" for q in data.get('questions', [])) if data.get('questions') else "- General information"}

This is just a test to verify agent creation works correctly.""",
            voice_id=data.get('voiceId', '21m00Tcm4TlvDq8ikWAM'),
            language="en",
            first_message=f"Hello! This is a test agent for {data.get('callPurpose', 'testing')}."
        )
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        agent_result = loop.run_until_complete(elevenlabs_client.create_agent(agent_config))
        loop.close()
        
        print(f"✅ Test agent created successfully: {agent_result.get('agent_id')}")
        
        return jsonify({
            'success': True,
            'agent_id': agent_result.get("agent_id"),
            'message': 'Test agent created successfully! Phone number is configured and ready for calls.',
            'agent_config': {
                'name': agent_config.name,
                'voice_id': agent_config.voice_id,
                'language': agent_config.language
            },
            'phone_number_configured': True,
            'phone_number_id': ELEVENLABS_PHONE_NUMBER_ID
        })
        
    except Exception as e:
        print(f"❌ Error creating test agent: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to create test agent'
        }), 500

@app.route('/api/call-status/<batch_call_id>', methods=['GET'])
def get_call_status(batch_call_id):
    """Get the status of a specific batch call with conversation results"""
    try:
        print(f"📋 Getting status for call: {batch_call_id}")
        
        if batch_call_id not in active_calls:
            return jsonify({
                "success": False,
                "message": "Call not found"
            }), 404
        
        local_info = active_calls[batch_call_id]
        
        # Get latest status from ElevenLabs
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Get batch call details
            batch_call_details = loop.run_until_complete(
                elevenlabs_client.get_batch_call_details(batch_call_id)
            )
            
            # Update local info with remote status
            local_info.update(batch_call_details)
            
            # If call is completed and we haven't processed it yet, try to get conversation details
            if (batch_call_details.get("status") == "completed" and 
                not local_info.get("conversation_processed", False) and 
                batch_call_id not in processed_calls):
                
                print(f"📞 Call completed, fetching conversation details...")
                processed_calls.add(batch_call_id)  # Mark as being processed
                
                try:
                    # Get conversations to find the one for this call
                    conversations = loop.run_until_complete(elevenlabs_client.get_conversations())
                    
                    # Find conversation for this batch call
                    conversation_found = False
                    for conversation in conversations.get("conversations", []):
                        if conversation.get("batch_call_id") == batch_call_id:
                            conversation_id = conversation.get("conversation_id")
                            print(f"📝 Found conversation: {conversation_id}")
                            
                            # Get conversation details
                            conversation_details = loop.run_until_complete(
                                elevenlabs_client.get_conversation_details(conversation_id)
                            )
                            
                            # Extract information from transcript
                            transcript = conversation_details.get("transcript", "")
                            questions = local_info.get("questions", [])
                            
                            extracted_info = extract_information_from_transcript(transcript, questions)
                            
                            # Store results
                            call_results[batch_call_id] = {
                                "conversation_id": conversation_id,
                                "transcript": transcript,
                                "extracted_info": extracted_info,
                                "conversation_details": conversation_details,
                                "processed_at": datetime.now().isoformat()
                            }
                            
                            local_info["conversation_results"] = call_results[batch_call_id]
                            local_info["conversation_processed"] = True
                            conversation_found = True
                            print(f"✅ Conversation results processed and stored")
                            break
                    
                    if not conversation_found:
                        print(f"⚠️  No conversation found for batch call {batch_call_id}")
                        # Don't mark as processed so we can try again later
                        processed_calls.discard(batch_call_id)
                        
                except Exception as conv_error:
                    print(f"⚠️  Error processing conversation: {conv_error}")
                    # Don't mark as processed so we can try again later
                    processed_calls.discard(batch_call_id)
            
            loop.close()
            
        except Exception as e:
            print(f"⚠️  Could not get remote status: {e}")
        
        return jsonify({
            "success": True,
            "batch_call_id": batch_call_id,
            "status": local_info.get("status", "unknown"),
            "call_info": local_info,
            "has_results": batch_call_id in call_results
        })
        
    except Exception as e:
        print(f"❌ Error getting call status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/call-results/<batch_call_id>', methods=['GET'])
def get_call_results(batch_call_id):
    """Get conversation results for a completed call"""
    try:
        if batch_call_id in call_results:
            return jsonify({
                "success": True,
                "batch_call_id": batch_call_id,
                "results": call_results[batch_call_id]
            })
        else:
            return jsonify({
                "success": False,
                "message": "No results found for this call"
            }), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/active-calls', methods=['GET'])
def get_active_calls():
    """Get all active calls with their current status"""
    try:
        # Update status for all active calls (but don't process conversations here to avoid loops)
        for batch_call_id in list(active_calls.keys()):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                batch_call_details = loop.run_until_complete(
                    elevenlabs_client.get_batch_call_details(batch_call_id)
                )
                # Only update status, don't process conversations here
                active_calls[batch_call_id]["status"] = batch_call_details.get("status", "unknown")
                loop.close()
            except Exception as e:
                print(f"⚠️  Could not update status for {batch_call_id}: {e}")
        
        return jsonify({
            "success": True,
            "active_calls": active_calls,
            "call_results": call_results
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/process-conversation/<batch_call_id>', methods=['POST'])
def process_conversation_manually(batch_call_id):
    """Manually trigger conversation processing for a completed call"""
    try:
        if batch_call_id not in active_calls:
            return jsonify({
                "success": False,
                "message": "Call not found"
            }), 404
        
        if batch_call_id in call_results:
            return jsonify({
                "success": True,
                "message": "Conversation already processed",
                "results": call_results[batch_call_id]
            })
        
        local_info = active_calls[batch_call_id]
        
        # Force conversation processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            conversations = loop.run_until_complete(elevenlabs_client.get_conversations())
            
            for conversation in conversations.get("conversations", []):
                if conversation.get("batch_call_id") == batch_call_id:
                    conversation_id = conversation.get("conversation_id")
                    print(f"📝 Processing conversation: {conversation_id}")
                    
                    conversation_details = loop.run_until_complete(
                        elevenlabs_client.get_conversation_details(conversation_id)
                    )
                    
                    transcript = conversation_details.get("transcript", "")
                    questions = local_info.get("questions", [])
                    
                    extracted_info = extract_information_from_transcript(transcript, questions)
                    
                    call_results[batch_call_id] = {
                        "conversation_id": conversation_id,
                        "transcript": transcript,
                        "extracted_info": extracted_info,
                        "conversation_details": conversation_details,
                        "processed_at": datetime.now().isoformat()
                    }
                    
                    local_info["conversation_results"] = call_results[batch_call_id]
                    local_info["conversation_processed"] = True
                    
                    loop.close()
                    
                    return jsonify({
                        "success": True,
                        "message": "Conversation processed successfully",
                        "results": call_results[batch_call_id]
                    })
            
            loop.close()
            return jsonify({
                "success": False,
                "message": "No conversation found for this call"
            }), 404
            
        except Exception as e:
            loop.close()
            raise e
            
    except Exception as e:
        print(f"❌ Error processing conversation: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/webhook', methods=['POST'])
def webhook_handler():
    """Handle webhooks from ElevenLabs"""
    try:
        webhook_data = request.get_json()
        print(f"🔔 Webhook received: {webhook_data.get('type', 'unknown')}")
        print(f"🔔 Webhook data: {json.dumps(webhook_data, indent=2)}")
        
        # Store webhook data
        webhook_id = webhook_data.get("id", f"webhook_{datetime.now().isoformat()}")
        conversation_data[webhook_id] = webhook_data
        
        # If this is a call completion webhook, mark for processing
        if webhook_data.get("type") == "conversation_ended":
            batch_call_id = webhook_data.get("batch_call_id")
            if batch_call_id and batch_call_id in active_calls:
                print(f"📞 Call {batch_call_id} ended via webhook")
                active_calls[batch_call_id]["status"] = "completed"
                # Don't process here to avoid webhook timeout, let the status endpoint handle it
        
        return jsonify({"status": "success"})
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/webhooks', methods=['GET'])
def get_webhooks():
    """Get all received webhooks for debugging"""
    return jsonify({
        "success": True,
        "webhooks": conversation_data
    })

# Custom 404 handler to suppress Socket.IO errors
@app.errorhandler(404)
def not_found(error):
    if '/socket.io/' in request.path:
        return '', 404
    print(f"⚠️  404 Not Found: {request.path}")
    return jsonify({"error": "Not found"}), 404

if __name__ == '__main__':
    print("🚀 Starting CEX Protocol AI Backend on http://0.0.0.0:5001")
    print("🔑 ElevenLabs API Key configured:", "Yes" if ELEVENLABS_API_KEY != 'your-api-key-here' else "No - Please set ELEVENLABS_API_KEY")
    print(f"📞 Phone Number ID configured: {ELEVENLABS_PHONE_NUMBER_ID}")
    print("\n✨ Server ready with fixed call tracking (no infinite loops)!\n")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
