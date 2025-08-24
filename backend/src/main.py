# backend/src/main.py - FIXED SCHEDULED_TIME_UNIX FIELD
# This version provides a proper timestamp for scheduled_time_unix

import os
import sys
import logging
import time

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import asyncio
import json
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

# Store active calls (in production, use a database)
active_calls = {}

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
        """Create a conversational AI agent using the CORRECT API endpoint"""
        async with httpx.AsyncClient() as client:
            # This is the correct payload structure based on ElevenLabs documentation
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
            
            # Use the CORRECT endpoint: /v1/convai/agents/create
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
        """Create a batch call using the CORRECT endpoint with proper timestamp"""
        async with httpx.AsyncClient() as client:
            # Get current Unix timestamp for immediate execution
            current_time = int(time.time())
            
            payload = {
                "call_name": f"AI Call to {phone_number}",
                "agent_id": agent_id,
                "agent_phone_number_id": ELEVENLABS_PHONE_NUMBER_ID,  # Your phone number ID
                "scheduled_time_unix": current_time,  # Use current timestamp for immediate execution
                "recipients": [
                    {
                        "phone_number": phone_number
                    }
                ]
            }
            
            print(f"🔍 Batch Call Payload: {json.dumps(payload, indent=2)}")
            
            # CORRECTED ENDPOINT: /v1/convai/batch-calling/submit
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
        """Get all batch calls using the correct endpoint"""
        async with httpx.AsyncClient() as client:
            # CORRECTED ENDPOINT: /v1/convai/batch-calling
            response = await client.get(
                f"{ELEVENLABS_BASE_URL}/convai/batch-calling",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to get batch calls: {response.status_code} - {response.text}")

# Initialize ElevenLabs client
elevenlabs_client = ElevenLabsClient(ELEVENLABS_API_KEY)

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
            voice_id=data.get('voice_id', '21m00Tcm4TlvDq8ikWAM'),  # Default voice
            language=data.get('language', 'en'),
            first_message=data.get('first_message')
        )
        
        # Run async function in sync context
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
    """Initiate an AI phone call using ElevenLabs batch calling"""
    try:
        data = request.get_json()
        print(f"📞 Make call request for: {data.get('phoneNumber')}")
        
        phone_number = data.get('phoneNumber')
        agent_id = data.get('agentId')
        
        if not phone_number:
            return jsonify({
                'success': False,
                'error': 'phoneNumber is required'
            }), 400
        
        # Create agent if needed
        if not agent_id or agent_id == "create_new":
            print("🤖 Creating new agent for call...")
            agent_config = AgentConfig(
                name=data.get('agentName', 'AI Assistant'),
                prompt=f"""You are {data.get('agentName', 'an AI assistant')} making a phone call for {data.get('callPurpose', 'information gathering')}.

Your goal is to have a natural conversation and gather the following information:
{chr(10).join(f"- {q}" for q in data.get('questions', [])) if data.get('questions') else "- General information as appropriate"}

Guidelines:
- Be polite and professional
- Introduce yourself and explain the purpose of the call
- Ask questions naturally in conversation
- Listen to responses and ask follow-up questions if needed
- Thank the person for their time at the end
- Keep the call concise but thorough

Start the conversation with a friendly greeting and introduction.""",
                voice_id=data.get('voiceId', '21m00Tcm4TlvDq8ikWAM'),
                language="en",
                first_message=f"Hello! This is {data.get('agentName', 'an AI assistant')}. I'm calling regarding {data.get('callPurpose', 'a brief survey')}. Do you have a few minutes to chat?"
            )
            
            # Create agent
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            agent_result = loop.run_until_complete(elevenlabs_client.create_agent(agent_config))
            agent_id = agent_result["agent_id"]
            loop.close()
            print(f"✅ Agent created: {agent_id}")
        
        # Now make the actual call using your phone number
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
            "questions": data.get('questions', []),
            "batch_call_data": call_result
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
        
        # Create agent
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

@app.route('/api/batch-calls', methods=['GET'])
def get_batch_calls():
    """Get all batch calls"""
    try:
        print("📋 Getting batch calls...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(elevenlabs_client.get_batch_calls())
        loop.close()
        
        return jsonify({
            "success": True,
            "batch_calls": result
        })
        
    except Exception as e:
        print(f"❌ Error getting batch calls: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/call-status/<batch_call_id>', methods=['GET'])
def get_call_status(batch_call_id):
    """Get the status of a specific batch call"""
    try:
        if batch_call_id in active_calls:
            local_info = active_calls[batch_call_id]
            
            # Get latest status from ElevenLabs
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                batch_calls = loop.run_until_complete(elevenlabs_client.get_batch_calls())
                loop.close()
                
                # Find our specific batch call
                for batch_call in batch_calls.get("batch_calls", []):
                    if batch_call.get("id") == batch_call_id:
                        local_info.update(batch_call)
                        break
                        
            except Exception as e:
                print(f"⚠️  Could not get remote status: {e}")
            
            return jsonify({
                "success": True,
                "batch_call_id": batch_call_id,
                "status": local_info.get("status", "unknown"),
                "call_info": local_info
            })
        else:
            return jsonify({
                "success": False,
                "message": "Call not found"
            }), 404
            
    except Exception as e:
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
        
        # Store webhook data for debugging
        webhook_id = webhook_data.get("id", f"webhook_{datetime.now().isoformat()}")
        active_calls[webhook_id] = webhook_data
        
        return jsonify({"status": "success"})
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/webhooks', methods=['GET'])
def get_webhooks():
    """Get all received webhooks for debugging"""
    return jsonify({
        "success": True,
        "webhooks": active_calls
    })

@app.route('/api/active-calls', methods=['GET'])
def get_active_calls():
    """Get all active calls"""
    return jsonify({
        "success": True,
        "active_calls": active_calls
    })

# Custom 404 handler to suppress Socket.IO errors
@app.errorhandler(404)
def not_found(error):
    # Don't log Socket.IO 404s
    if '/socket.io/' in request.path:
        return '', 404
    print(f"⚠️  404 Not Found: {request.path}")
    return jsonify({"error": "Not found"}), 404

if __name__ == '__main__':
    print("🚀 Starting CEX Protocol AI Backend on http://0.0.0.0:5001")
    print("🔑 ElevenLabs API Key configured:", "Yes" if ELEVENLABS_API_KEY != 'your-api-key-here' else "No - Please set ELEVENLABS_API_KEY")
    print(f"📞 Phone Number ID configured: {ELEVENLABS_PHONE_NUMBER_ID}")
    print("\n✨ Server ready! You can now make actual phone calls!\n")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
