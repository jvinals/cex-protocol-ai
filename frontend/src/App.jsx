// frontend/src/App.jsx - VERSION WITH AGENT TESTING
// Replace your current App.jsx with this

import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Phone, PhoneCall, Loader2, TestTube, CheckCircle } from 'lucide-react'
import './App.css'

function App() {
  const [phoneNumber, setPhoneNumber] = useState('+34699043286')
  const [agentId, setAgentId] = useState('create_new')
  const [callPurpose, setCallPurpose] = useState('Customer Survey')
  const [questions, setQuestions] = useState('What is your name?\nWhat is your email address?\nHow satisfied are you with our service?')
  const [callStatus, setCallStatus] = useState('idle')
  const [callResults, setCallResults] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [currentConversationId, setCurrentConversationId] = useState(null)
  const [statusMessage, setStatusMessage] = useState('')
  const [testAgentResult, setTestAgentResult] = useState(null)

  const testBackendConnection = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/test')
      const data = await response.json()
      alert(`✅ Backend connection successful: ${data.message}`)
    } catch (error) {
      alert(`❌ Backend connection failed: ${error.message}`)
    }
  }

  const testAgentCreation = async () => {
    setIsLoading(true)
    setStatusMessage('Testing agent creation...')
    
    try {
      const response = await fetch('http://localhost:5001/api/test-agent-creation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agentName: 'Test AI Survey Agent',
          callPurpose: callPurpose,
          questions: questions.split('\n').filter(q => q.trim()),
          voiceId: '21m00Tcm4TlvDq8ikWAM'
        }),
      })

      const data = await response.json()
      console.log('Test agent response:', data)

      if (data.success) {
        setTestAgentResult(data)
        setStatusMessage('✅ Agent created successfully! Ready for phone calls.')
        setAgentId(data.agent_id) // Use the created agent for calls
      } else {
        setStatusMessage(`❌ Agent creation failed: ${data.message || data.error}`)
        alert(`Agent creation failed: ${data.message || data.error}`)
      }
    } catch (error) {
      console.error('Error testing agent creation:', error)
      setStatusMessage('❌ Error testing agent creation: ' + error.message)
      alert('Error testing agent creation: ' + error.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleMakeCall = async () => {
    if (!phoneNumber) {
      alert('Please enter a phone number')
      return
    }

    setIsLoading(true)
    setCallStatus('initiating')
    setCallResults(null)
    setStatusMessage('Preparing to make call...')

    try {
      const response = await fetch('http://localhost:5001/api/make-call', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phoneNumber: phoneNumber,
          agentId: agentId === 'create_new' ? null : agentId,
          agentName: 'AI Survey Agent',
          callPurpose: callPurpose,
          questions: questions.split('\n').filter(q => q.trim()),
          voiceId: '21m00Tcm4TlvDq8ikWAM'
        }),
      })

      const data = await response.json()
      console.log('Call response:', data)

      if (data.success) {
        setCallStatus('initiated')
        setCurrentConversationId(data.conversation_id)
        setStatusMessage('Call initiated successfully!')
      } else {
        setCallStatus('failed')
        setStatusMessage(`Call setup info: ${data.message}`)
        
        // Show helpful setup information
        if (data.next_steps) {
          const steps = data.next_steps.join('\n')
          alert(`Phone number setup required:\n\n${steps}`)
        } else {
          alert(`Call failed: ${data.message || data.error}`)
        }
      }
    } catch (error) {
      console.error('Error making call:', error)
      setCallStatus('failed')
      setStatusMessage('Error making call: ' + error.message)
      alert('Error making call: ' + error.message)
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'idle': return 'secondary'
      case 'initiating': return 'default'
      case 'initiated': return 'default'
      case 'in_progress': return 'default'
      case 'completed': return 'default'
      case 'failed': return 'destructive'
      default: return 'secondary'
    }
  }

  const getStatusText = (status) => {
    switch (status) {
      case 'idle': return 'Ready'
      case 'initiating': return 'Starting call...'
      case 'initiated': return 'Call initiated'
      case 'in_progress': return 'Call in progress'
      case 'completed': return 'Call completed'
      case 'failed': return 'Call failed'
      default: return status
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="text-center py-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            CEX Protocol AI Phone System
          </h1>
          <p className="text-lg text-gray-600">
            Make AI-powered phone calls using ElevenLabs Conversational AI
          </p>
          <div className="flex gap-2 justify-center mt-4">
            <Button 
              onClick={testBackendConnection} 
              variant="outline" 
              size="sm"
            >
              Test Backend
            </Button>
            <Button 
              onClick={testAgentCreation} 
              variant="outline" 
              size="sm"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Testing...
                </>
              ) : (
                <>
                  <TestTube className="mr-2 h-4 w-4" />
                  Test Agent Creation
                </>
              )}
            </Button>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Call Configuration */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Phone className="h-5 w-5" />
                Call Configuration
              </CardTitle>
              <CardDescription>
                Configure your AI phone call settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Phone Number *
                </label>
                <Input
                  type="tel"
                  placeholder="+1234567890"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Agent ID
                </label>
                <Input
                  placeholder="create_new (recommended)"
                  value={agentId}
                  onChange={(e) => setAgentId(e.target.value)}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Use "create_new" or test agent creation first
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Call Purpose
                </label>
                <Input
                  placeholder="Customer satisfaction survey"
                  value={callPurpose}
                  onChange={(e) => setCallPurpose(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Questions (one per line)
                </label>
                <Textarea
                  placeholder="What is your name?&#10;What is your email address?&#10;How satisfied are you with our service?"
                  value={questions}
                  onChange={(e) => setQuestions(e.target.value)}
                  rows={4}
                />
              </div>

              <Button 
                onClick={handleMakeCall} 
                disabled={isLoading || callStatus === 'in_progress'}
                className="w-full"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Making Call...
                  </>
                ) : (
                  <>
                    <PhoneCall className="mr-2 h-4 w-4" />
                    Make Call
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Call Status & Results */}
          <Card>
            <CardHeader>
              <CardTitle>Status & Results</CardTitle>
              <CardDescription>
                System status and call information
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Current Status
                </label>
                <Badge variant={getStatusColor(callStatus)} className="text-sm">
                  {getStatusText(callStatus)}
                </Badge>
                {statusMessage && (
                  <p className="text-sm text-gray-600 mt-1">{statusMessage}</p>
                )}
              </div>

              {testAgentResult && (
                <div className="bg-green-50 p-3 rounded-md">
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span className="font-medium text-green-800">Agent Created Successfully</span>
                  </div>
                  <div className="text-sm text-green-700 space-y-1">
                    <p><strong>Agent ID:</strong> {testAgentResult.agent_id}</p>
                    <p><strong>Name:</strong> {testAgentResult.agent_config?.name}</p>
                    <p><strong>Voice:</strong> {testAgentResult.agent_config?.voice_id}</p>
                  </div>
                </div>
              )}

              {currentConversationId && (
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Conversation ID
                  </label>
                  <p className="text-xs text-gray-600 font-mono bg-gray-50 p-2 rounded">
                    {currentConversationId}
                  </p>
                </div>
              )}

              {callResults && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Call Duration
                    </label>
                    <p className="text-sm text-gray-600">
                      {callResults.duration ? `${callResults.duration} seconds` : 'N/A'}
                    </p>
                  </div>

                  {callResults.extracted_data && Object.keys(callResults.extracted_data).length > 0 && (
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Extracted Information
                      </label>
                      <div className="bg-gray-50 p-3 rounded-md">
                        {Object.entries(callResults.extracted_data).map(([key, value]) => (
                          <div key={key} className="flex justify-between py-1">
                            <span className="font-medium capitalize">{key}:</span>
                            <span>{value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {callResults.full_transcript && (
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Full Transcript
                      </label>
                      <div className="bg-gray-50 p-3 rounded-md max-h-40 overflow-y-auto">
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">
                          {callResults.full_transcript}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {callStatus === 'idle' && !testAgentResult && (
                <div className="text-center py-8 text-gray-500">
                  <TestTube className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>Start by testing the backend connection and agent creation</p>
                </div>
              )}

              {(callStatus === 'initiating' || callStatus === 'initiated' || callStatus === 'in_progress') && (
                <div className="text-center py-8">
                  <Loader2 className="h-12 w-12 mx-auto mb-2 animate-spin text-blue-500" />
                  <p className="text-gray-600">
                    {callStatus === 'initiating' && 'Preparing to make call...'}
                    {callStatus === 'initiated' && 'Call initiated, waiting for connection...'}
                    {callStatus === 'in_progress' && 'Call in progress...'}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Setup Instructions */}
        <Card>
          <CardHeader>
            <CardTitle>Setup Instructions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm text-gray-600">
              <p><strong>Step 1:</strong> Click "Test Backend" to verify the backend is running</p>
              <p><strong>Step 2:</strong> Set your ElevenLabs API key: <code>export ELEVENLABS_API_KEY="your_key"</code></p>
              <p><strong>Step 3:</strong> Click "Test Agent Creation" to verify ElevenLabs integration</p>
              <p><strong>Step 4:</strong> Configure a phone number in <a href="https://elevenlabs.io/app/conversational-ai" target="_blank" className="text-blue-600 underline">ElevenLabs Dashboard</a></p>
              <p><strong>Step 5:</strong> Update the backend with your phone number ID</p>
              <p><strong>Step 6:</strong> Enter a valid phone number and click "Make Call"</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default App
