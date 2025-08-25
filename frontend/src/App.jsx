// frontend/src/App.jsx - UPDATED VERSION BASED ON CURRENT REPOSITORY
// This version builds on your existing code and adds call tracking and conversation results functionality
// Handles conversation results better and provides manual processing option

import { useState, useEffect } from 'react'
import './App.css'

function App() {
  // Existing state from your current repository
  const [phoneNumber, setPhoneNumber] = useState('+34699043286')
  const [agentConfig, setAgentConfig] = useState({
    name: 'Standard Basic Protocol',
    purpose: 'General follow-up',
    questions: [
      'I\'ve noticed that you have been improving lately, thats awesome!. On a scale from 1 to 10, how are you feeling today?',
      'Are you keeping up with Lisinopril as instructed?',
      'In the past week, how often have you had symptoms like headaches, dizziness, or swelling?',
      'Have you noticed any new or different symptoms since we last spoke?',
      'Is there anything else you\'d like Dr. Vinals to know about how you\'ve been feeling?'
    ],
    voiceId: 'EXAVITQu4vr4xnSDxMaL', // Default voice
    language: 'en',
    firstMessage: 'Hi, I\'m the AI assistant of Dr. Vinals. I\'m calling to follow up on you and to ask if there are any concerns.',
    customPrompt: 'You are a professional AI assistant calling on behalf of Dr. Vinals. Be polite, professional, and empathetic. Start with the greeting (firstMessage), and don\'t wait for the patient to answer if he doesn\'t, just continue with the first question. If the patient has problems please help him. At the end you shpuld return a JSON object with the results of the call in an strctured way.'
  })
  
  // New state for call tracking and results
  const [callStatus, setCallStatus] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [currentCall, setCurrentCall] = useState(null)
  const [callResults, setCallResults] = useState(null)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [activeCalls, setActiveCalls] = useState({})
  const [pollingInterval, setPollingInterval] = useState(null)
  const [debugInfo, setDebugInfo] = useState(null)
  const [showDebug, setShowDebug] = useState(false)

  // Available voices (you can expand this list)
  const availableVoices = [
    { id: '21m00Tcm4TlvDq8ikWAM', name: 'Rachel' },
    { id: 'AZnzlk1XvdvUeBnXmlld', name: 'Domi' },
    { id: 'EXAVITQu4vr4xnSDxMaL', name: 'Bella (Default)' },
    { id: 'ErXwobaYiN019PkySvjV', name: 'Antoni' },
    { id: 'MF3mGyEYCl7XYWbV9V6O', name: 'Elli' },
    { id: 'TxGEqnHWrfWFTfGW9XjX', name: 'Josh' },
    { id: 'VR6AewLTigWG4xSOukaG', name: 'Arnold' },
    { id: 'pNInz6obpgDQGcFmaJgB', name: 'Adam' }
  ]

  // Agent templates based on your current repository structure
  const agentTemplates = {
    'standard_protocol': {
      name: 'Standard Basic Protocol',
      purpose: 'General follow-up',
      questions: [
        'I\'ve noticed that you have been improving lately, thats awesome!. On a scale from 1 to 10, how are you feeling today?',
        'Are you keeping up with Lisinopril as instructed?',
        'In the past week, how often have you had symptoms like headaches, dizziness, or swelling?',
        'Have you noticed any new or different symptoms since we last spoke?',
        'Is there anything else you\'d like Dr. Vinals to know about how you\'ve been feeling?'
      ],
      firstMessage: 'Hi, I\'m the AI assistant of Dr. Vinals. I\'m calling to follow up on you and to ask if there are any concerns.'
    },
    'hypertension_protocol': {
      name: 'Hypertension Protocol',
      purpose: 'Follow up on hypertension patients',
      questions: [
        'I\'ve noticed that you have been improving lately, thats awesome!. On a scale from 1 to 10, how are you feeling today?',
        'Are you keeping up with Lisinopril as instructed?',
        'What about Losartan?',
        'In the past week, how often have you had symptoms like headaches, dizziness, or swelling?',
        'Have you noticed any new or different symptoms since we last spoke?',
        'Is there anything else you\'d like Dr. Vinals to know about how you\'ve been feeling?'
      ],
      firstMessage: 'Hi, I\'m the AI assistant of Dr. Vinals. I\'m calling to follow up on you and to ask if there are any concerns.'
    },
    'diabetes_protocol': {
      name: 'Diabetes Protocol',
      purpose: 'Follow up on diabetes patients',
      questions: [
        'I\'ve noticed that you have been improving lately, thats awesome!. On a scale from 1 to 10, how are you feeling with Losartan as instructed?',
        'Are you keeping up with Losartan as instructed?',
        'In the past week, how often have you had symptoms like headaches, dizziness, or swelling?',
        'Have you noticed any new or different symptoms since we last spoke?',
        'Is there anything else you\'d like Dr. Vinals to know about how you\'ve been feeling?'
      ],
      firstMessage: 'Hi, I\'m the AI assistant of Dr. Vinals. I\'m calling to follow up on you and to ask if there are any concerns.'
    },
    'asthma_protocol': {
      name: 'Asthma Protocol',
      purpose: 'Follow up on asthmatic patients',
      questions: [
        'I\'ve noticed that you have been improving lately, thats awesome!. On a scale from 1 to 10, how are you feeling with Losartan as instructed?',
        'Are you keeping up with Losartan as instructed?',
        'In the past week, how often have you had symptoms like headaches, dizziness, or swelling?',
        'Have you noticed any new or different symptoms since we last spoke?',
        'Is there anything else you\'d like Dr. Vinals to know about how you\'ve been feeling?'
      ],
      firstMessage: 'Hi, I\'m the AI assistant of Dr. Vinals. I\'m calling to follow up on you and to ask if there are any concerns.'
    }
  }

  // Poll for call status updates with better handling
  useEffect(() => {
    if (currentCall && !pollingInterval) {
      const interval = setInterval(async () => {
        try {
          const response = await fetch(`http://localhost:5001/api/call-status/${currentCall.batch_call_id}`)
          const data = await response.json()
          
          if (data.success) {
            const status = data.call_info.status
            setCallStatus(`📞 Call Status: ${formatCallStatus(status)}`)
            
            // Update current call info
            setCurrentCall(prev => ({
              ...prev,
              status: status,
              call_info: data.call_info
            }))
            
            // If call is completed, show message but don't auto-process
            if (status === 'completed') {
              if (data.call_info.conversation_results) {
                setCallResults(data.call_info.conversation_results)
                setCallStatus('✅ Call completed! Results available below.')
                clearInterval(interval)
                setPollingInterval(null)
              } else {
                setCallStatus('✅ Call completed! Click "Get Results" to fetch the conversation.')
              }
            } else if (status === 'failed' || status === 'cancelled') {
              setCallStatus(`❌ Call ${status}`)
              clearInterval(interval)
              setPollingInterval(null)
            }
          }
        } catch (error) {
          console.error('Error polling call status:', error)
        }
      }, 5000) // Poll every 5 seconds
      
      setPollingInterval(interval)
    }
    
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval)
        setPollingInterval(null)
      }
    }
  }, [currentCall, pollingInterval])

  // Load active calls on component mount
  useEffect(() => {
    loadActiveCalls()
  }, [])

  const loadActiveCalls = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/active-calls')
      const data = await response.json()
      
      if (data.success) {
        setActiveCalls(data.active_calls)
      }
    } catch (error) {
      console.error('Error loading active calls:', error)
    }
  }

  const testBackend = async () => {
    setIsLoading(true)
    setCallStatus('Testing backend connection...')
    
    try {
      const response = await fetch('http://localhost:5001/api/test')
      const data = await response.json()
      
      if (response.ok) {
        setCallStatus('✅ Backend connection successful!')
      } else {
        setCallStatus('❌ Backend test failed')
      }
    } catch (error) {
      setCallStatus('❌ Cannot connect to backend. Make sure the server is running on port 5001.')
    }
    
    setIsLoading(false)
  }

  const testAgentCreation = async () => {
    setIsLoading(true)
    setCallStatus('Testing agent creation...')
    
    try {
      const response = await fetch('http://localhost:5001/api/test-agent-creation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agentName: agentConfig.name,
          callPurpose: agentConfig.purpose,
          questions: agentConfig.questions,
          voiceId: agentConfig.voiceId
        }),
      })
      
      const data = await response.json()
      console.log('Test agent response:', data)
      
      if (data.success) {
        setCallStatus(`✅ Test agent created successfully! Agent ID: ${data.agent_id}`)
      } else {
        setCallStatus(`❌ Agent creation failed: ${data.error}`)
      }
    } catch (error) {
      setCallStatus('❌ Error testing agent creation')
    }
    
    setIsLoading(false)
  }

  const makeCall = async () => {
    if (!phoneNumber.trim()) {
      setCallStatus('❌ Please enter a phone number')
      return
    }

    setIsLoading(true)
    setCallStatus('Initiating call...')
    setCallResults(null) // Clear previous results
    setDebugInfo(null) // Clear debug info
    
    // Clear any existing polling
    if (pollingInterval) {
      clearInterval(pollingInterval)
      setPollingInterval(null)
    }
    
    try {
      const response = await fetch('http://localhost:5001/api/make-call', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phoneNumber: phoneNumber,
          agentId: 'create_new',
          agentName: agentConfig.name,
          callPurpose: agentConfig.purpose,
          questions: agentConfig.questions,
          voiceId: agentConfig.voiceId,
          firstMessage: agentConfig.firstMessage,
          customPrompt: agentConfig.customPrompt
        }),
      })
      
      const data = await response.json()
      console.log('Call response:', data)
      
      if (data.success) {
        setCallStatus(`✅ Call initiated! Tracking progress...`)
        setCurrentCall({
          batch_call_id: data.batch_call_id,
          agent_id: data.agent_id,
          phone_number: phoneNumber,
          status: 'initiated',
          start_time: new Date().toISOString()
        })
      } else {
        setCallStatus(`❌ Call failed: ${data.error}`)
      }
    } catch (error) {
      setCallStatus('❌ Error making call')
    }
    
    setIsLoading(false)
  }

  const getCallResults = async () => {
    if (!currentCall) {
      setCallStatus('❌ No active call to get results for')
      return
    }

    setIsLoading(true)
    setCallStatus('Fetching conversation results...')
    
    try {
      // Try to manually process the conversation
      const response = await fetch(`http://localhost:5001/api/process-conversation/${currentCall.batch_call_id}`, {
        method: 'POST'
      })
      
      const data = await response.json()
      
      if (data.success) {
        setCallResults(data.results)
        setCallStatus('✅ Conversation results retrieved!')
        setDebugInfo(null) // Clear debug info on success
      } else {
        setCallStatus(`❌ Could not get results: ${data.message}`)
        if (data.debug_info) {
          setDebugInfo(data.debug_info)
        }
      }
    } catch (error) {
      setCallStatus('❌ Error fetching results')
    }
    
    setIsLoading(false)
  }

  const debugConversations = async () => {
    setIsLoading(true)
    setCallStatus('Fetching all conversations for debugging...')
    
    try {
      const response = await fetch('http://localhost:5001/api/debug-conversations')
      const data = await response.json()
      
      if (data.success) {
        setDebugInfo(data.conversations)
        setCallStatus('✅ Debug information retrieved! Check the debug section below.')
        setShowDebug(true)
      } else {
        setCallStatus(`❌ Could not get debug info: ${data.error}`)
      }
    } catch (error) {
      setCallStatus('❌ Error fetching debug info')
    }
    
    setIsLoading(false)
  }

  const loadTemplate = (templateKey) => {
    const template = agentTemplates[templateKey]
    setAgentConfig({
      ...agentConfig,
      name: template.name,
      purpose: template.purpose,
      questions: template.questions,
      firstMessage: template.firstMessage
    })
    setCallStatus(`✅ Loaded template: ${template.name}`)
  }

  const addQuestion = () => {
    setAgentConfig({
      ...agentConfig,
      questions: [...agentConfig.questions, '']
    })
  }

  const updateQuestion = (index, value) => {
    const newQuestions = [...agentConfig.questions]
    newQuestions[index] = value
    setAgentConfig({
      ...agentConfig,
      questions: newQuestions
    })
  }

  const removeQuestion = (index) => {
    const newQuestions = agentConfig.questions.filter((_, i) => i !== index)
    setAgentConfig({
      ...agentConfig,
      questions: newQuestions
    })
  }

  const formatCallStatus = (status) => {
    const statusMap = {
      'pending': '⏳ Pending',
      'in_progress': '📞 In Progress',
      'completed': '✅ Completed',
      'failed': '❌ Failed',
      'cancelled': '🚫 Cancelled'
    }
    return statusMap[status] || status
  }

  const stopPolling = () => {
    if (pollingInterval) {
      clearInterval(pollingInterval)
      setPollingInterval(null)
      setCallStatus('⏸️ Stopped tracking call status')
    }
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>🤖 CEX Protocol AI Phone System</h1>
        <p>Configure your AI agent and make intelligent phone calls</p>
      </header>

      <main className="main-content">
        {/* Agent Configuration Section */}
        <section className="config-section">
          <h2>🎯 Agent Configuration</h2>
          
          {/* Quick Templates */}
          <div className="templates">
            <h3>Protocol Templates:</h3>
            <div className="template-buttons">
              {Object.entries(agentTemplates).map(([key, template]) => (
                <button 
                  key={key}
                  onClick={() => loadTemplate(key)}
                  className="template-btn"
                >
                  {template.name}
                </button>
              ))}
            </div>
          </div>

          {/* Basic Configuration */}
          <div className="config-group">
            <label>
              Agent Name:
              <input
                type="text"
                value={agentConfig.name}
                onChange={(e) => setAgentConfig({...agentConfig, name: e.target.value})}
                placeholder="AI Survey Agent"
              />
            </label>

            <label>
              Call Purpose:
              <input
                type="text"
                value={agentConfig.purpose}
                onChange={(e) => setAgentConfig({...agentConfig, purpose: e.target.value})}
                placeholder="Customer Survey"
              />
            </label>

            <label>
              Voice:
              <select
                value={agentConfig.voiceId}
                onChange={(e) => setAgentConfig({...agentConfig, voiceId: e.target.value})}
              >
                {availableVoices.map(voice => (
                  <option key={voice.id} value={voice.id}>
                    {voice.name}
                  </option>
                ))}
              </select>
            </label>

            <label>
              First Message:
              <textarea
                value={agentConfig.firstMessage}
                onChange={(e) => setAgentConfig({...agentConfig, firstMessage: e.target.value})}
                placeholder="Hello! I'm calling regarding..."
                rows="2"
              />
            </label>
          </div>

          {/* Questions Configuration */}
          <div className="questions-section">
            <h3>Questions to Ask:</h3>
            {agentConfig.questions.map((question, index) => (
              <div key={index} className="question-item">
                <textarea
                  value={question}
                  onChange={(e) => updateQuestion(index, e.target.value)}
                  placeholder={`Question ${index + 1}`}
                  rows="2"
                />
                <button 
                  onClick={() => removeQuestion(index)}
                  className="remove-btn"
                >
                  ❌
                </button>
              </div>
            ))}
            <button onClick={addQuestion} className="add-btn">
              ➕ Add Question
            </button>
          </div>

          {/* Advanced Configuration */}
          <div className="advanced-section">
            <button 
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="toggle-btn"
            >
              {showAdvanced ? '🔼' : '🔽'} Advanced Configuration
            </button>
            
            {showAdvanced && (
              <div className="advanced-config">
                <label>
                  Custom Prompt (Optional):
                  <textarea
                    value={agentConfig.customPrompt}
                    onChange={(e) => setAgentConfig({...agentConfig, customPrompt: e.target.value})}
                    placeholder="Override the default prompt with your custom instructions..."
                    rows="4"
                  />
                </label>
                
                <label>
                  Language:
                  <select
                    value={agentConfig.language}
                    onChange={(e) => setAgentConfig({...agentConfig, language: e.target.value})}
                  >
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                    <option value="it">Italian</option>
                  </select>
                </label>
              </div>
            )}
          </div>
        </section>

        {/* Phone Call Section */}
        <section className="call-section">
          <h2>📞 Make Phone Call</h2>
          
          <div className="phone-input">
            <label>
              Phone Number:
              <input
                type="tel"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                placeholder="+1234567890"
              />
            </label>
          </div>

          <div className="action-buttons">
            <button 
              onClick={testBackend} 
              disabled={isLoading}
              className="test-btn"
            >
              {isLoading ? '⏳' : '🔧'} Test Backend
            </button>
            
            <button 
              onClick={testAgentCreation} 
              disabled={isLoading}
              className="test-btn"
            >
              {isLoading ? '⏳' : '🤖'} Test Agent Creation
            </button>
            
            <button 
              onClick={makeCall} 
              disabled={isLoading || !phoneNumber.trim()}
              className="call-btn"
            >
              {isLoading ? '⏳ Calling...' : '📞 Make Call'}
            </button>
          </div>

          {callStatus && (
            <div className="status-message">
              {callStatus}
            </div>
          )}

          {/* Current Call Tracking */}
          {currentCall && (
            <div className="current-call">
              <h3>📞 Current Call</h3>
              <div className="call-info">
                <p><strong>Phone:</strong> {currentCall.phone_number}</p>
                <p><strong>Status:</strong> {formatCallStatus(currentCall.status)}</p>
                <p><strong>Call ID:</strong> {currentCall.batch_call_id}</p>
                <p><strong>Agent ID:</strong> {currentCall.agent_id}</p>
                <p><strong>Started:</strong> {new Date(currentCall.start_time).toLocaleString()}</p>
              </div>
              
              <div className="call-actions">
                <button 
                  onClick={getCallResults}
                  disabled={isLoading}
                  className="results-btn"
                >
                  {isLoading ? '⏳ Getting Results...' : '📋 Get Results'}
                </button>
                
                <button 
                  onClick={debugConversations}
                  disabled={isLoading}
                  className="debug-btn"
                >
                  {isLoading ? '⏳ Debugging...' : '🔍 Debug Conversations'}
                </button>
                
                {pollingInterval && (
                  <button 
                    onClick={stopPolling}
                    className="stop-btn"
                  >
                    ⏸️ Stop Tracking
                  </button>
                )}
              </div>
            </div>
          )}
        </section>

        {/* Debug Information Section */}
        {debugInfo && (
          <section className="debug-section">
            <h2>🔍 Debug Information</h2>
            <button 
              onClick={() => setShowDebug(!showDebug)}
              className="toggle-btn"
            >
              {showDebug ? '🔼' : '🔽'} {showDebug ? 'Hide' : 'Show'} Debug Details
            </button>
            
            {showDebug && (
              <div className="debug-content">
                <pre>{JSON.stringify(debugInfo, null, 2)}</pre>
              </div>
            )}
            
            {debugInfo.batch_call_id && (
              <div className="debug-summary">
                <h3>Debug Summary:</h3>
                <p><strong>Looking for Batch Call ID:</strong> {debugInfo.batch_call_id}</p>
                <p><strong>Agent ID:</strong> {debugInfo.agent_id}</p>
                <p><strong>Total Conversations Found:</strong> {debugInfo.total_conversations}</p>
                <p><strong>Fetch Attempts:</strong> {debugInfo.attempts}/5</p>
              </div>
            )}
          </section>
        )}

        {/* Call Results Section */}
        {callResults && (
          <section className="results-section">
            <h2>📋 Conversation Results</h2>
            
            <div className="results-content">
              <div className="extracted-info">
                <h3>📊 Extracted Information</h3>
                {Object.entries(callResults.extracted_info).map(([key, info]) => (
                  <div key={key} className="info-item">
                    <strong>Q: {info.question}</strong>
                    <p>A: {info.answer}</p>
                  </div>
                ))}
              </div>
              
              <div className="transcript">
                <h3>📝 Full Transcript</h3>
                <div className="transcript-content">
                  {callResults.transcript || 'No transcript available'}
                </div>
              </div>
              
              <div className="metadata">
                <h3>ℹ️ Call Metadata</h3>
                <p><strong>Conversation ID:</strong> {callResults.conversation_id}</p>
                <p><strong>Processed At:</strong> {new Date(callResults.processed_at).toLocaleString()}</p>
                {callResults.note && (
                  <p><strong>Note:</strong> {callResults.note}</p>
                )}
              </div>
            </div>
          </section>
        )}

        {/* Active Calls Section */}
        {Object.keys(activeCalls).length > 0 && (
          <section className="active-calls-section">
            <h2>📞 Recent Calls</h2>
            <div className="calls-list">
              {Object.entries(activeCalls).map(([callId, callInfo]) => (
                <div key={callId} className="call-item">
                  <div className="call-header">
                    <strong>{callInfo.phone_number || 'Unknown'}</strong>
                    <span className="call-status">{formatCallStatus(callInfo.status)}</span>
                  </div>
                  <div className="call-details">
                    <p>Agent: {callInfo.agent_name || 'Unknown'}</p>
                    <p>Purpose: {callInfo.purpose || 'Unknown'}</p>
                    <p>Started: {callInfo.start_time ? new Date(callInfo.start_time).toLocaleString() : 'Unknown'}</p>
                    <p>Call ID: {callId}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Configuration Preview */}
        <section className="preview-section">
          <h2>👀 Agent Preview</h2>
          <div className="preview-content">
            <p><strong>Name:</strong> {agentConfig.name}</p>
            <p><strong>Purpose:</strong> {agentConfig.purpose}</p>
            <p><strong>Voice:</strong> {availableVoices.find(v => v.id === agentConfig.voiceId)?.name}</p>
            <p><strong>Questions ({agentConfig.questions.length}):</strong></p>
            <ul>
              {agentConfig.questions.map((q, i) => (
                <li key={i}>{q || `Question ${i + 1} (empty)`}</li>
              ))}
            </ul>
            {agentConfig.firstMessage && (
              <p><strong>First Message:</strong> "{agentConfig.firstMessage}"</p>
            )}
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
