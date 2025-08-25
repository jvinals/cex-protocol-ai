# backend/src/main.py - COMPLETE VERSION WITH AGENT CONFIGURATION FIXES
# This version properly incorporates questions, first messages, and conversation flow

import os
import sys
import logging
import time
import re
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import httpx
from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import BaseModel

# Disable Flask's default request logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf6G5gvasqr$S$MG'

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
        """Create a new conversational AI agent"""
        url = f"{ELEVENLABS_BASE_URL}/convai/agents/create"
        
        payload = {
            "name": config.name,
            "conversation_config": {
                "agent": {
                    "prompt": {
                        "prompt": config.prompt
                    },
                    "first_message": config.first_message or f"Hi, I'm {config.name}. How can I help you today?",
                    "language": config.language
                },
                "asr": {
                    "quality": "high"
                },
                "tts": {
                    "voice_id": config.voice_id
                }
            }
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=self.headers)
                print(f"🔍 Agent Creation - Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "agent_id": result.get("agent_id"),
                        "agent": result
                    }
                else:
                    error_text = response.text
                    print(f"❌ Agent creation failed: {response.status_code} - {error_text}")
                    return {
                        "success": False,
                        "error": f"Failed to create agent: {response.status_code} - {error_text}"
                    }
            except Exception as e:
                print(f"❌ Exception creating agent: {str(e)}")
                return {
                    "success": False,
                    "error": f"Exception creating agent: {str(e)}"
                }

    async def create_batch_call(self, agent_id: str, phone_number: str, call_name: str) -> Dict:
        """Create a batch call"""
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
            try:
                response = await client.post(url, json=payload, headers=self.headers)
                print(f"🔍 Batch Call - Status: {response.status_code}")
                print(f"🔍 Batch Call - Response: {response.text}")
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "batch_call_id": result.get("id"),
                        "batch_call": result
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to create batch call: {response.status_code} - {response.text}"
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Exception creating batch call: {str(e)}"
                }

    async def get_batch_call_status(self, batch_call_id: str) -> Dict:
        """Get batch call status"""
        url = f"{ELEVENLABS_BASE_URL}/convai/batch-calling/{batch_call_id}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "status": result.get("status"),
                        "batch_call": result
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to get batch call status: {response.status_code} - {response.text}"
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Exception getting batch call status: {str(e)}"
                }

    async def get_conversations(self) -> Dict:
        """Get all conversations"""
        url = f"{ELEVENLABS_BASE_URL}/convai/conversations"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "conversations": result.get("conversations", [])
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to get conversations: {response.status_code} - {response.text}"
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Exception getting conversations: {str(e)}"
                }

    async def get_conversation_by_id(self, conversation_id: str) -> Dict:
        """Get conversation details by ID"""
        url = f"{ELEVENLABS_BASE_URL}/convai/conversations/{conversation_id}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "conversation": result
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to get conversation: {response.status_code} - {response.text}"
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Exception getting conversation: {str(e)}"
                }

# Initialize ElevenLabs client
elevenlabs_client = ElevenLabsClient(ELEVENLABS_API_KEY)

# 1. Start: Use your first message to greet the person and don't wait for an answer and move to the questions, just continue immediately without a pause

def build_structured_prompt(agent_config: dict) -> str:
    """Build an optimized prompt that works better with ElevenLabs conversational AI"""
    
    base_prompt = agent_config.get('prompt', 'You are a helpful AI assistant.')
    questions = agent_config.get('questions', [])
    agent_name = agent_config.get('name', 'AI Assistant')
    call_purpose = agent_config.get('purpose', 'General follow-up')
    
    # ElevenLabs works better with more direct, conversational prompts
    # Avoid overly complex instructions that might confuse the AI
    
    if questions:
        # Create a more natural, conversational prompt
        structured_prompt = f"""You are {agent_name}, calling for {call_purpose}.

CONVERSATION SCRIPT - Follow this exact sequence:

1. Then ask these questions ONE AT A TIME, waiting for each answer:

"""
        
        # Add questions in a simple, numbered format
        for i, question in enumerate(questions, 1):
            structured_prompt += f"   {i}. {question}\n"
        
        structured_prompt += f"""
2. After all questions: Thank them and end the call
3. Create a JSON object with the results of the call in an structured way.

IMPORTANT RULES:
- Ask only ONE question at a time
- Wait for their complete answer before asking the next question
- If they don't understand, rephrase the question simply
- Be patient and friendly
- Don't rush through the questions
- After getting all {len(questions)} answers, say thank you and goodbye

CONVERSATION STYLE:
- Be natural and conversational
- Show empathy and understanding
- Keep your responses brief between questions
- Focus on getting clear answers to each question
"""
        
        # Add custom prompt as additional context if provided
        if base_prompt and base_prompt != 'You are a helpful AI assistant.' and base_prompt != f"You are {agent_name}, a professional AI assistant calling to {call_purpose}.":
            structured_prompt += f"\nADDITIONAL INSTRUCTIONS:\n{base_prompt}"
    
    else:
        # If no questions, use a simpler prompt
        structured_prompt = f"""You are {agent_name}, calling for {call_purpose}.

Have a natural, friendly conversation. Be professional and helpful.

{base_prompt if base_prompt != 'You are a helpful AI assistant.' else ''}
"""
    
    return structured_prompt

def build_first_message(agent_config: dict) -> str:
    """Build a proper first message that sets up the conversation"""
    
    first_message = agent_config.get('firstMessage', '')
    agent_name = agent_config.get('name', 'AI Assistant')
    call_purpose = agent_config.get('purpose', 'follow up')
    questions = agent_config.get('questions', [])
    
    # If no first message provided, create one
    if not first_message:
        if questions:
            first_message = f"Hi, I'm {agent_name}. I'm calling to {call_purpose}. I have a few questions that will only take a couple of minutes. Is now a good time to talk?"
        else:
            first_message = f"Hi, I'm {agent_name}. I'm calling to {call_purpose}. How are you doing today?"
    
    return first_message

# Enhanced agent templates with better conversation flow
def get_agent_templates():
    return {
        "standard_protocol": {
            "name": "Standard Basic Protocol",
            "purpose": "General follow-up",
            "questions": [
                "I've noticed that you have been improving lately, thats awesome!. On a scale from 1 to 10, how are you feeling?",
                "Are you keeping up with Lisinopril as instructed?",
                "In the past week, how often have you had symptoms like headaches, dizziness, or swelling?",
                "Have you noticed any new or different symptoms since we last spoke?",
                "Is there anything else you'd like Dr. Vinals to know about how you've been feeling?"
            ],
            "voice_id": "21m00Tcm4TlvDq8ikWAM",
            "language": "en",
            "first_message": "Hi, I'm the AI assistant of Dr. Vinals. I'm calling to follow up on you and to ask if there are any changes in your health since your last visit. I have a few quick questions that will only take a couple of minutes. Is now a good time?",
            "custom_prompt": "You are a professional AI assistant calling on behalf of Dr. Vinals. You must ask each question one at a time and wait for complete responses. Be polite, professional, and empathetic. If a patient needs clarification, rephrase the question. Keep the conversation focused on getting answers to all the questions."
        },
        "hypertension_protocol": {
            "name": "Hypertension Protocol",
            "purpose": "Hypertension follow-up",
            "questions": [
                "I've noticed that you have been improving lately, thats awesome!. On a scale from 1 to 10, how are you feeling?",
                "Are you keeping up with Lisinopril as instructed?",
                "In the past week, how often have you had symptoms like headaches, dizziness, or swelling?",
                "Have you noticed any new or different symptoms since we last spoke?",
                "Is there anything else you'd like Dr. Vinals to know about how you've been feeling?"
            ],
            "voice_id": "EXAVITQu4vr4xnSDxMaL",
            "language": "en",
            "first_message": "Hi, I'm the AI assistant of Dr. Vinals. I'm calling to follow up on your hypertension treatment and see how you're doing. I have a few questions about your medication and symptoms. Is this a good time to talk?",
            "custom_prompt": "You are a professional AI assistant calling on behalf of Dr. Vinals for a hypertension follow-up. Ask each question individually and wait for responses. Be understanding about medical concerns and encourage patients to be honest about their symptoms and medication compliance."
        },
        "diabetes_protocol": {
            "name": "Diabetes Protocol", 
            "purpose": "Diabetes follow-up",
            "questions": [
                "I've noticed that you have been improving lately, thats awesome!. On a scale from 1 to 10, how are you feeling?",
                "Are you keeping up with Losartan as instructed?",
                "In the past week, how often have you had symptoms like headaches, dizziness, or swelling?",
                "Have you noticed any new or different symptoms since we last spoke?",
                "Is there anything else you'd like Dr. Vinals to know about how you've been feeling?"
            ],
            "voice_id": "21m00Tcm4TlvDq8ikWAM",
            "language": "en",
            "first_message": "Hi, I'm the AI assistant of Dr. Vinals. I'm calling to check on your diabetes management and see how you're feeling. I have some questions about your medication and any symptoms you might be experiencing. Do you have a few minutes to talk?",
            "custom_prompt": "You are a professional AI assistant calling on behalf of Dr. Vinals for a diabetes follow-up. Focus on medication compliance and symptom monitoring. Ask questions one at a time and be patient with responses. Show empathy for any challenges the patient might be facing."
        }
    }

# Extract information from transcript - handles both string and list formats
def extract_information_from_transcript(transcript, questions: List[str]) -> Dict:
    """Extract structured information from conversation transcript - FIXED VERSION"""
    extracted_info = {}
    
    # Handle both string and list transcript formats
    if isinstance(transcript, list):
        # If transcript is a list, join all parts into a single string
        transcript_text = " ".join([str(item) for item in transcript if item])
    elif isinstance(transcript, str):
        transcript_text = transcript
    else:
        # Fallback for other types
        transcript_text = str(transcript) if transcript else ""
    
    # Convert transcript to lowercase for easier matching
    transcript_lower = transcript_text.lower()
    
    print(f"🔍 Processing transcript (length: {len(transcript_text)} chars)")
    print(f"📝 Transcript preview: {transcript_text[:200]}...")
    
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
            match = re.search(email_pattern, transcript_text)  # Use original case for email
            if match:
                answer = match.group(1)
        
        # Look for satisfaction/rating patterns
        elif any(word in question.lower() for word in ["satisfied", "satisfaction", "rating", "scale"]):
            rating_patterns = [
                r"(\d+)\s*out of\s*\d+",
                r"(\d+)\s*/\s*\d+",
                r"rate.*?(\d+)",
                r"(\d+)\s*(?:stars?|points?)",
                r"scale.*?(\d+)",
                r"feeling.*?(\d+)"
            ]
            for pattern in rating_patterns:
                match = re.search(pattern, transcript_lower)
                if match:
                    answer = f"{match.group(1)}/10"
                    break
        
        # Look for medication patterns (for medical protocols)
        elif any(word in question.lower() for word in ["medication", "medicine", "lisinopril", "losartan"]):
            if any(word in transcript_lower for word in ["yes", "taking", "keep up", "continue", "prescribed"]):
                answer = "Yes, taking as prescribed"
            elif any(word in transcript_lower for word in ["no", "stopped", "not taking", "quit"]):
                answer = "No, not taking medication"
            elif any(word in transcript_lower for word in ["sometimes", "occasionally", "forget"]):
                answer = "Taking inconsistently"
        
        # Look for symptoms patterns
        elif "symptom" in question.lower():
            symptoms = []
            if "headache" in transcript_lower:
                symptoms.append("headaches")
            if "dizziness" in transcript_lower or "dizzy" in transcript_lower:
                symptoms.append("dizziness")
            if "swelling" in transcript_lower or "swollen" in transcript_lower:
                symptoms.append("swelling")
            if "fatigue" in transcript_lower or "tired" in transcript_lower:
                symptoms.append("fatigue")
            if "nausea" in transcript_lower:
                symptoms.append("nausea")
            
            if symptoms:
                answer = ", ".join(symptoms)
            else:
                answer = "No specific symptoms mentioned"
        
        # Look for frequency patterns (how often)
        elif "how often" in question.lower() or "frequency" in question.lower():
            frequency_patterns = [
                r"(\d+)\s*times?\s*(?:a|per)\s*(?:day|week|month)",
                r"(?:every|each)\s*(\w+)",
                r"(daily|weekly|monthly|rarely|never|always|often|sometimes)"
            ]
            for pattern in frequency_patterns:
                match = re.search(pattern, transcript_lower)
                if match:
                    answer = match.group(1) if match.group(1) else match.group(0)
                    break
        
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
        
        print(f"📊 Q{i+1}: {question[:50]}... -> A: {answer}")
    
    return extracted_info

async def find_conversation_for_call(batch_call_id: str, agent_id: str) -> Dict:
    """Find conversation associated with a batch call"""
    try:
        # Get all conversations
        conversations_result = await elevenlabs_client.get_conversations()
        
        if not conversations_result["success"]:
            return {
                "success": False,
                "message": "Failed to fetch conversations",
                "debug_info": conversations_result.get("error")
            }
        
        conversations = conversations_result["conversations"]
        print(f"📋 Found {len(conversations)} total conversations")
        
        # Try to find conversation by batch_call_id first
        for conv in conversations:
            if conv.get("batch_call_id") == batch_call_id:
                print(f"✅ Found conversation by batch_call_id: {conv.get('conversation_id')}")
                return {
                    "success": True,
                    "conversation": conv
                }
        
        # If not found by batch_call_id, try by agent_id
        for conv in conversations:
            if conv.get("agent_id") == agent_id:
                print(f"✅ Found conversation by agent_id: {conv.get('conversation_id')}")
                return {
                    "success": True,
                    "conversation": conv
                }
        
        # Debug info
        debug_info = {
            "total_conversations": len(conversations),
            "looking_for_batch_call_id": batch_call_id,
            "looking_for_agent_id": agent_id,
            "available_batch_call_ids": [conv.get("batch_call_id") for conv in conversations if conv.get("batch_call_id")],
            "available_agent_ids": [conv.get("agent_id") for conv in conversations if conv.get("agent_id")]
        }
        
        return {
            "success": False,
            "message": f"No conversation found for batch call {batch_call_id}",
            "debug_info": debug_info
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error finding conversation: {str(e)}",
            "debug_info": {"error": str(e)}
        }

# Custom 404 handler to suppress Socket.IO logs
@app.errorhandler(404)
def handle_404(e):
    if request.path.startswith('/socket.io'):
        return '', 404
    return jsonify({"error": "Not found"}), 404

@app.route('/')
def root():
    return jsonify({"message": "CEX Protocol AI Backend API"})

@app.route('/api/test')
def test_backend():
    print("✅ Backend test endpoint called successfully")
    return jsonify({
        "success": True,
        "message": "Backend connection successful",
        "elevenlabs_configured": bool(ELEVENLABS_API_KEY and ELEVENLABS_API_KEY != 'your-api-key-here'),
        "phone_number_configured": bool(ELEVENLABS_PHONE_NUMBER_ID)
    })

@app.route('/api/test-agent-creation', methods=['POST'])
def test_agent_creation():
    try:
        print("🧪 Testing agent creation: Test AI Assistant")
        
        # Create a test agent configuration
        test_config = AgentConfig(
            name="Test AI Assistant",
            prompt="You are a helpful AI assistant for testing purposes. Be friendly and professional.",
            voice_id="21m00Tcm4TlvDq8ikWAM",
            language="en",
            first_message="Hello! This is a test call from the AI assistant."
        )
        
        # Create the agent
        result = asyncio.run(elevenlabs_client.create_agent(test_config))
        
        if result["success"]:
            agent_id = result["agent_id"]
            print(f"✅ Test agent created successfully: {agent_id}")
            return jsonify({
                "success": True,
                "message": "Test agent created successfully",
                "agent_id": agent_id,
                "elevenlabs_configured": bool(ELEVENLABS_API_KEY and ELEVENLABS_API_KEY != 'your-api-key-here'),
                "phone_number_configured": bool(ELEVENLABS_PHONE_NUMBER_ID)
            })
        else:
            print(f"❌ Test agent creation failed: {result['error']}")
            return jsonify({
                "success": False,
                "message": "Failed to create test agent",
                "error": result["error"]
            }), 500
            
    except Exception as e:
        print(f"❌ Exception in test agent creation: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Exception in test agent creation",
            "error": str(e)
        }), 500

@app.route('/api/agent-templates')
def get_templates():
    return jsonify({
        "success": True,
        "templates": get_agent_templates()
    })

@app.route('/api/make-call', methods=['POST'])
def make_call():
    try:
        data = request.get_json()
        print(f"📞 Make call request for: {data.get('phoneNumber')}")
        
        # Extract data from the correct locations (root level, not nested in agentConfig)
        phone_number = data.get('phoneNumber')
        agent_name = data.get('agentName', 'AI Assistant')
        call_purpose = data.get('callPurpose', 'follow up with you')
        questions = data.get('questions', [])
        voice_id = data.get('voiceId', '21m00Tcm4TlvDq8ikWAM')
        first_message = data.get('firstMessage', '')
        custom_prompt = data.get('customPrompt', '')
        language = data.get('language', 'en')
        
        print(f"🤖 Creating agent: {agent_name}")
        print(f"📋 Call purpose: {call_purpose}")
        print(f"📝 Questions count: {len(questions)}")
        print(f"💬 First message: {first_message}")
        print(f"📜 Custom prompt length: {len(custom_prompt)} chars")
        print(f"📜 Custom prompt: {custom_prompt}")
        print(f"🎤 Voice ID: {voice_id}")
        
        if not phone_number:
            return jsonify({
                "success": False,
                "message": "Phone number is required"
            }), 400
        
        # Create agent config dictionary for prompt building
        agent_config = {
            'name': agent_name,
            'purpose': call_purpose,
            'questions': questions,
            'firstMessage': first_message,
            'prompt': custom_prompt if custom_prompt else f"You are {agent_name}, a professional AI assistant calling to {call_purpose}."
        }
        
        # Build the structured prompt that incorporates questions
        structured_prompt = build_structured_prompt(agent_config)
        print(f"🔍 Generated prompt length: {len(structured_prompt)} characters")
        print(f"📝 Prompt preview: {structured_prompt}...")
        
        # Use the provided first message or build one
        if first_message:
            final_first_message = first_message
        else:
            final_first_message = build_first_message(agent_config)
        
        print(f"💬 Final first message: {final_first_message}")
        
        print("🤖 Creating new agent for call...")
        
        # Create agent configuration with structured prompt
        config = AgentConfig(
            name=agent_name,
            prompt=structured_prompt,  # Use the structured prompt that includes questions
            voice_id=voice_id,
            language=language,
            first_message=final_first_message
        )
        
        # Create the agent
        agent_result = asyncio.run(elevenlabs_client.create_agent(config))
        
        if not agent_result["success"]:
            print(f"❌ Agent creation failed: {agent_result['error']}")
            return jsonify({
                "success": False,
                "message": "Failed to create agent",
                "error": agent_result["error"]
            }), 500
        
        agent_id = agent_result["agent_id"]
        print(f"✅ Agent created: {agent_id}")
        
        # Create batch call
        call_name = f"AI Call to {phone_number}"
        print(f"📞 Initiating call to {phone_number} with agent {agent_id}")
        
        batch_call_result = asyncio.run(elevenlabs_client.create_batch_call(agent_id, phone_number, call_name))
        
        if not batch_call_result["success"]:
            print(f"❌ Error making call: {batch_call_result['error']}")
            return jsonify({
                "success": False,
                "message": "Failed to initiate call",
                "error": batch_call_result["error"]
            }), 500
        
        batch_call_id = batch_call_result["batch_call_id"]
        print(f"✅ Call initiated successfully: {batch_call_id}")
        
        # Store call information with enhanced details
        active_calls[batch_call_id] = {
            "phone_number": phone_number,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "call_purpose": call_purpose,
            "questions": questions,
            "first_message": final_first_message,
            "custom_prompt": custom_prompt,
            "structured_prompt": structured_prompt,
            "voice_id": voice_id,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "conversation_processed": False
        }
        
        return jsonify({
            "success": True,
            "message": "Call initiated successfully",
            "batch_call_id": batch_call_id,
            "agent_id": agent_id,
            "agent_config": {
                "name": agent_name,
                "purpose": call_purpose,
                "questions_count": len(questions),
                "first_message": final_first_message,
                "voice_id": voice_id
            }
        })
        
    except Exception as e:
        print(f"❌ Error making call: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": "Failed to initiate call",
            "error": str(e)
        }), 500

@app.route('/api/call-status/<batch_call_id>')
def get_call_status(batch_call_id):
    try:
        print(f"📋 Getting status for call: {batch_call_id}")
        
        if batch_call_id not in active_calls:
            return jsonify({
                "success": False,
                "message": "Call not found"
            }), 404
        
        # Get status from ElevenLabs
        status_result = asyncio.run(elevenlabs_client.get_batch_call_status(batch_call_id))
        
        if status_result["success"]:
            status = status_result["status"]
            active_calls[batch_call_id]["status"] = status
            
            # Only return status, don't process conversation automatically
            
            return jsonify({
                "success": True,
                "status": status,
                "call_info": active_calls[batch_call_id],
                "results": call_results.get(batch_call_id),
                "conversation_processed": active_calls[batch_call_id].get("conversation_processed", False)
            })
        else:
            return jsonify({
                "success": False,
                "message": "Failed to get call status",
                "error": status_result["error"]
            }), 500
            
    except Exception as e:
        print(f"❌ Error getting call status: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to get call status",
            "error": str(e)
        }), 500

@app.route('/api/process-conversation/<batch_call_id>', methods=['POST'])
def process_conversation(batch_call_id):
    """Manually process conversation for a specific call - FIXED VERSION"""
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
        
        # Find conversation
        conversation_result = asyncio.run(find_conversation_for_call(batch_call_id, agent_id))
        
        if not conversation_result["success"]:
            return jsonify({
                "success": False,
                "message": conversation_result["message"],
                "debug_info": conversation_result.get("debug_info")
            }), 404
        
        conversation = conversation_result["conversation"]
        conversation_id = conversation.get("conversation_id")
        
        print(f"🔍 Found conversation: {conversation_id}")
        
        # Get full conversation details
        conv_details_result = asyncio.run(elevenlabs_client.get_conversation_by_id(conversation_id))
        
        if conv_details_result["success"]:
            conv_details = conv_details_result["conversation"]
            
            # Enhanced transcript handling for different formats
            raw_transcript = conv_details.get("transcript", "No transcript available")
            
            print(f"🔍 Raw transcript type: {type(raw_transcript)}")
            print(f"🔍 Raw transcript content: {str(raw_transcript)[:200]}...")
            
            # Process transcript based on its format
            if isinstance(raw_transcript, list):
                # If it's a list, try to extract text from each item
                transcript_parts = []
                for item in raw_transcript:
                    if isinstance(item, dict):
                        # If item is a dict, look for common text fields
                        text = item.get('text', item.get('content', item.get('message', str(item))))
                        transcript_parts.append(str(text))
                    else:
                        transcript_parts.append(str(item))
                transcript = " ".join(transcript_parts)
            elif isinstance(raw_transcript, dict):
                # If it's a dict, look for common text fields
                transcript = raw_transcript.get('text', raw_transcript.get('content', str(raw_transcript)))
            else:
                # If it's already a string or other type
                transcript = str(raw_transcript) if raw_transcript else "No transcript available"
            
            print(f"📝 Processed transcript: {transcript[:300]}...")
            
        else:
            transcript = "Could not retrieve transcript"
            print(f"❌ Failed to get conversation details: {conv_details_result.get('error', 'Unknown error')}")
        
        # Enhanced error handling for information extraction
        try:
            extracted_info = extract_information_from_transcript(transcript, questions)
            print(f"✅ Successfully extracted information for {len(extracted_info)} questions")
        except Exception as e:
            print(f"❌ Error extracting information: {str(e)}")
            # Fallback: create basic extracted info
            extracted_info = {}
            for i, question in enumerate(questions):
                extracted_info[f"question_{i+1}"] = {
                    "question": question,
                    "answer": "Could not extract answer due to processing error"
                }
        
        # Store results
        results = {
            "conversation_id": conversation_id,
            "transcript": transcript,
            "extracted_info": extracted_info,
            "processed_at": datetime.now().isoformat(),
            "raw_transcript_type": str(type(raw_transcript)),
            "processing_notes": f"Transcript was {type(raw_transcript).__name__} format, converted to string"
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
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to process conversation"
        }), 500

@app.route('/api/debug-conversations')
def debug_conversations():
    """Debug endpoint to see all available conversations"""
    try:
        conversations_result = asyncio.run(elevenlabs_client.get_conversations())
        
        if conversations_result["success"]:
            conversations = conversations_result["conversations"]
            
            debug_info = {
                "total_conversations": len(conversations),
                "conversations": []
            }
            
            for conv in conversations:
                debug_info["conversations"].append({
                    "conversation_id": conv.get("conversation_id"),
                    "agent_id": conv.get("agent_id"),
                    "batch_call_id": conv.get("batch_call_id"),
                    "status": conv.get("status"),
                    "created_at": conv.get("created_at")
                })
            
            return jsonify({
                "success": True,
                "debug_info": debug_info
            })
        else:
            return jsonify({
                "success": False,
                "error": conversations_result["error"]
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/call-results/<batch_call_id>')
def get_call_results(batch_call_id):
    try:
        if batch_call_id not in call_results:
            return jsonify({
                "success": False,
                "message": "No results found for this call"
            }), 404
        
        return jsonify({
            "success": True,
            "results": call_results[batch_call_id]
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/active-calls')
def get_active_calls():
    return jsonify({
        "success": True,
        "active_calls": active_calls,
        "call_results": call_results
    })

if __name__ == '__main__':
    print("🚀 Starting CEX Protocol AI Backend on http://0.0.0.0:5001")
    api_key_configured = bool(ELEVENLABS_API_KEY and ELEVENLABS_API_KEY != 'your-api-key-here')
    print(f"🔑 ElevenLabs API Key configured: {'Yes' if api_key_configured else 'No - Please set ELEVENLABS_API_KEY'}")
    print("✨ Server ready! Logs will show important events only.")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
