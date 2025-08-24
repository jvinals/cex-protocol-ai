import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Phone, PhoneCall, Loader2 } from 'lucide-react'
import io from 'socket.io-client'
import './App.css'

// Create socket connection outside component to prevent recreation
const socket = io('http://localhost:5001', {
  transports: ['websocket', 'polling']
})

function App() {
  const [phoneNumber, setPhoneNumber] = useState('+34699043286')
  const [agentId, setAgentId] = useState('test-agent')
  const [callPurpose, setCallPurpose] = useState('Customer Survey')
  const [questions, setQuestions] = useState('What is your name?\nWhat is your email address?\nHow satisfied are you with our service?')
  const [callStatus, setCallStatus] = useState('idle')
  const [callResults, setCallResults] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    console.log('Setting up Socket.IO event listeners...')

    socket.on('connect', () => {
      console.log('Connected to server')
    })

    socket.on('disconnect', () => {
      console.log('Disconnected from server')
    })

    socket.on('call_update', (data) => {
      console.log('Call update received:', data)
      setCallStatus(data.status || 'unknown')
      if (data.results) {
        setCallResults(data.results)
      }
    })

    socket.on('error', (error) => {
      console.error('Socket.IO error:', error)
    })

    socket.on('test_event', (data) => {
      console.log('Test event received:', data)
    })

    // Clean up event listeners when component unmounts
    return () => {
      console.log('Cleaning up Socket.IO event listeners...')
      socket.off('connect')
      socket.off('disconnect')
      socket.off('call_update')
      socket.off('error')
      socket.off('test_event')
    }
  }, [])

  const handleMakeCall = async () => {
    console.log('Attempting to making call with phone number:', phoneNumber, 'and agent ID:', agentId)
    if (!phoneNumber || !agentId) {
      alert('Please fill in phone number and agent ID')
      return
    }

    setIsLoading(true)
    setCallStatus('initiating')
    setCallResults(null)

    try {
      console.log('Hitting the API make-call endpoint');
      const response = await fetch('http://localhost:5001/api/make-call', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phoneNumber,
          agentId,
          callPurpose,
          questions: questions.split('\n').filter(q => q.trim())
        }),
      })

      const data = await response.json()
      console.log('API response:', data)
      
      if (data.success) {
        console.log('Data success');
        console.log('Data:', data);
        setCallStatus(data.status || 'initiated')
        console.log('Status updated to:', data.status || 'initiated')
      } else {
        setCallStatus('failed')
        alert(`Call failed: ${data.message}`)
      }
    } catch (error) {
      console.error('Error making call:', error)
      setCallStatus('failed')
      alert('Failed to initiate call')
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="text-center py-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            AI Phone Call System
          </h1>
          <p className="text-lg text-gray-600">
            Make intelligent phone calls with AI agents to gather information
          </p>
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
                Set up your AI phone call parameters
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Phone Number</label>
                <Input
                  type="tel"
                  placeholder="+1234567890"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                />
              </div>
              
              <div>
                <label className="text-sm font-medium mb-2 block">Agent ID</label>
                <Input
                  placeholder="your-elevenlabs-agent-id"
                  value={agentId}
                  onChange={(e) => setAgentId(e.target.value)}
                />
              </div>
              
              <div>
                <label className="text-sm font-medium mb-2 block">Call Purpose</label>
                <Input
                  placeholder="e.g., Customer survey, Information gathering"
                  value={callPurpose}
                  onChange={(e) => setCallPurpose(e.target.value)}
                />
              </div>
              
              <div>
                <label className="text-sm font-medium mb-2 block">Questions (one per line)</label>
                <Textarea
                  placeholder="What is your name?&#10;What is your email address?&#10;How satisfied are you with our service?"
                  value={questions}
                  onChange={(e) => setQuestions(e.target.value)}
                  rows={4}
                />
              </div>
              
              <Button 
                onClick={handleMakeCall} 
                disabled={isLoading || !phoneNumber || !agentId}
                className="w-full"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Initiating Call...
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

          {/* Call Status and Results */}
          <Card>
            <CardHeader>
              <CardTitle>Call Status & Results</CardTitle>
              <CardDescription>
                Real-time updates and extracted information
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Current Status</label>
                <Badge variant={getStatusColor(callStatus)} className="text-sm">
                  {callStatus.replace('_', ' ').toUpperCase()}
                </Badge>
              </div>
              
              {callResults && (
                <div className="space-y-3">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Extracted Information</label>
                    <div className="bg-gray-50 p-3 rounded-md">
                      <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                        {JSON.stringify(callResults, null, 2)}
                      </pre>
                    </div>
                  </div>
                </div>
              )}
              
              {callStatus === 'idle' && (
                <div className="text-center py-8 text-gray-500">
                  <Phone className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>Configure your call settings and click "Make Call" to begin</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default App
