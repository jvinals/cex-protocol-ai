from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import requests
import os
import time
from twilio.rest import Client
from config import ELEVENLABS_API_KEY, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER

phone_calls_bp = Blueprint('phone_calls', __name__)

@phone_calls_bp.route('/test', methods=['GET'])
def test():
    """Test endpoint to verify routing is working"""
    return jsonify({'message': 'Phone calls blueprint is working!'})

@phone_calls_bp.route('/test-socket', methods=['GET'])
def test_socket():
    """Test Socket.IO connection"""
    from src.main import sio
    print("Testing Socket.IO connection")
    sio.emit('test_event', {'message': 'Socket.IO test successful'})
    return jsonify({'message': 'Socket.IO test event sent'})

# ElevenLabs API configuration
ELEVENLABS_BASE_URL = 'https://api.elevenlabs.io/v1'

@phone_calls_bp.route('/make-call', methods=['POST'])
@cross_origin()
def make_call():
    """Initiate an AI phone call using ElevenLabs API"""
    print("Received make-call request")
    print(f"ELEVENLABS_API_KEY: {ELEVENLABS_API_KEY}")
    try:
        data = request.get_json()
        print(f"Request data: {data}")
        phone_number = data.get('phoneNumber')
        agent_id = data.get('agentId')
        
        if not phone_number or not agent_id:
            return jsonify({'error': 'phoneNumber and agentId are required'}), 400
        
        # Prepare the request to ElevenLabs Batch Calling API
        headers = {
            'Authorization': f'Bearer {ELEVENLABS_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # This is a simplified example - you'll need to adapt to the actual ElevenLabs API
        payload = {
            'phone_number': phone_number,
            'agent_id': agent_id,
            'metadata': {
                'call_purpose': data.get('callPurpose', 'Information gathering'),
                'questions': data.get('questions', [])
            }
        }
        
        # Initialize Twilio client
        if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
            return jsonify({
                'success': False,
                'error': 'Twilio credentials not configured',
                'message': 'Please set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER in your .env file'
            }), 400
        
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        try:
            # Make the actual phone call using Twilio
            print(f"Making Twilio call to {phone_number}")
            
            # Create an interactive TwiML for the call
            twiml = f"""
            <Response>
                <Gather input="speech" action="/api/handle-response" method="POST" speechTimeout="auto" language="en-US">
                    <Say voice="alice">Hello! This is an AI phone call. The purpose of this call is: {data.get('callPurpose', 'Information gathering')}. 
                    I have some questions for you. Please answer after the beep.</Say>
                </Gather>
                <Say voice="alice">Thank you for your time!</Say>
            </Response>
            """
            
            # Make the call
            call = client.calls.create(
                twiml=twiml,
                to=phone_number,
                from_=TWILIO_PHONE_NUMBER
            )
            
            call_id = call.sid
            
            print(f"Twilio call initiated with SID: {call_id}")
            
            # Emit Socket.IO event to update frontend
            from src.main import sio
            print(f"Emitting Socket.IO event: call_update with data: {{'call_id': '{call_id}', 'status': 'initiated'}}")
            
            try:
                sio.emit('call_update', {
                    'call_id': call_id,
                    'status': 'initiated',
                    'message': 'Call initiated successfully'
                }, room=None)
                print("Socket.IO event emitted to all clients")
            except Exception as e:
                print(f"Error emitting Socket.IO event: {e}")
            
            return jsonify({
                'success': True,
                'call_id': call_id,
                'status': 'initiated',
                'message': 'Call initiated successfully via Twilio'
            })
            
        except Exception as e:
            print(f"Error making Twilio call: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'message': 'Failed to initiate call via Twilio'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to initiate call'
        }), 500

# Store conversation data (in production, use a database)
conversation_store = {}

@phone_calls_bp.route('/handle-response', methods=['POST'])
def handle_response():
    """Handle user responses during the call"""
    try:
        # Get the user's speech input
        speech_result = request.form.get('SpeechResult', '')
        confidence = request.form.get('Confidence', '0')
        call_sid = request.form.get('CallSid', '')
        
        print(f"User said: {speech_result} (confidence: {confidence})")
        
        # Store the conversation
        if call_sid not in conversation_store:
            conversation_store[call_sid] = {
                'responses': [],
                'questions': [],
                'start_time': time.time()
            }
        
        conversation_store[call_sid]['responses'].append({
            'question': 'User response',
            'answer': speech_result,
            'confidence': confidence,
            'timestamp': time.time()
        })
        
        # Here you would integrate with an AI service to generate a response
        # For now, we'll create a simple response
        ai_response = f"I heard you say: {speech_result}. Thank you for your response!"
        
        # Create TwiML response
        twiml = f"""
        <Response>
            <Gather input="speech" action="/api/handle-response" method="POST" speechTimeout="auto" language="en-US">
                <Say voice="alice">{ai_response}</Say>
            </Gather>
            <Say voice="alice">Thank you for your time!</Say>
        </Response>
        """
        
        return twiml, 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        print(f"Error handling response: {e}")
        return "Error", 500

@phone_calls_bp.route('/call-results/<call_id>', methods=['GET'])
def get_call_results(call_id):
    """Get the results of a specific call"""
    try:
        if call_id in conversation_store:
            conversation = conversation_store[call_id]
            
            # Process the conversation into structured data
            results = {
                'call_id': call_id,
                'status': 'completed',
                'duration': time.time() - conversation['start_time'],
                'total_responses': len(conversation['responses']),
                'responses': conversation['responses'],
                'summary': {
                    'questions_asked': len(conversation['questions']),
                    'responses_received': len(conversation['responses']),
                    'average_confidence': sum(float(r['confidence']) for r in conversation['responses']) / len(conversation['responses']) if conversation['responses'] else 0
                }
            }
            
            return jsonify(results)
        else:
            return jsonify({'error': 'Call not found'}), 404
            
    except Exception as e:
        print(f"Error retrieving call results: {e}")
        return jsonify({'error': str(e)}), 500

@phone_calls_bp.route('/webhook', methods=['POST'])
def webhook_handler():
    """Handle webhooks from ElevenLabs"""
    try:
        data = request.get_json()
        
        # Log the webhook data
        print(f"Received webhook: {data}")
        
        # Process different types of webhook events
        event_type = data.get('event_type')
        call_id = data.get('call_id')
        
        if event_type == 'call_started':
            # Handle call started event
            print(f"Call {call_id} started")
        elif event_type == 'call_ended':
            # Handle call ended event
            print(f"Call {call_id} ended")
            # Process the final transcript and generate JSON
            transcript = data.get('transcript', '')
            extracted_info = process_transcript(transcript)
            
            # Here you would typically save to database or emit via WebSocket
            print(f"Extracted information: {extracted_info}")
        elif event_type == 'speech_update':
            # Handle real-time speech updates
            print(f"Speech update for call {call_id}: {data.get('text', '')}")
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def process_transcript(transcript):
    """Process the call transcript and extract structured information"""
    # This is a simplified example - you would implement more sophisticated
    # natural language processing here
    
    extracted_info = {
        'transcript': transcript,
        'timestamp': request.json.get('timestamp'),
        'call_duration': request.json.get('duration'),
        'extracted_data': {
            'name': extract_name(transcript),
            'contact_info': extract_contact_info(transcript),
            'responses': extract_responses(transcript)
        }
    }
    
    return extracted_info

def extract_name(transcript):
    """Extract name from transcript"""
    # Simple implementation - you would use more sophisticated NLP
    import re
    name_pattern = r"my name is (\w+)"
    match = re.search(name_pattern, transcript.lower())
    return match.group(1) if match else None

def extract_contact_info(transcript):
    """Extract contact information from transcript"""
    # Simple implementation for email extraction
    import re
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, transcript)
    return {'emails': emails}

def extract_responses(transcript):
    """Extract specific responses to questions"""
    # This would be customized based on your specific questions
    return {
        'full_transcript': transcript,
        'key_points': []  # You would implement logic to extract key points
    }

