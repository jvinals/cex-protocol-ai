// frontend/src/App.jsx - ENHANCED VERSION WITH AGENT CONFIGURATION
// This version includes comprehensive agent configuration options

import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [phoneNumber, setPhoneNumber] = useState('')
  const [agentConfig, setAgentConfig] = useState({
    name: 'AI Survey Agent',
    purpose: 'Customer Survey',
    questions: [
      'What is your name?',
      'What is your email address?',
      'How satisfied are you with our service?'
    ],
    voiceId: '21m00Tcm4TlvDq8ikWAM', // Default voice
    language: 'en',
    firstMessage: '',
    customPrompt: ''
  })
  const [callStatus, setCallStatus] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [lastCallId, setLastCallId] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)

  // Available voices (you can expand this list)
  const availableVoices = [
    { id: '21m00Tcm4TlvDq8ikWAM', name: 'Rachel (Default)' },
    { id: 'AZnzlk1XvdvUeBnXmlld', name: 'Domi' },
    { id: 'EXAVITQu4vr4xnSDxMaL', name: 'Bella' },
    { id: 'ErXwobaYiN019PkySvjV', name: 'Antoni' },
    { id: 'MF3mGyEYCl7XYWbV9V6O', name: 'Elli' },
    { id: 'TxGEqnHWrfWFTfGW9XjX', name: 'Josh' },
    { id: 'VR6AewLTigWG4xSOukaG', name: 'Arnold' },
    { id: 'pNInz6obpgDQGcFmaJgB', name: 'Adam' }
  ]

  // Agent templates
  const agentTemplates = {
    'customer_survey': {
      name: 'Customer Survey Agent',
      purpose: 'Customer satisfaction survey',
      questions: [
        'What is your name?',
        'What is your email address?',
        'How satisfied are you with our service on a scale of 1-10?',
        'What could we improve?'
      ],
      firstMessage: 'Hello! I\'m calling to conduct a brief customer satisfaction survey. Do you have 3-4 minutes to help us improve our service?'
    },
    'appointment_booking': {
      name: 'Appointment Booking Agent',
      purpose: 'Schedule appointments',
      questions: [
        'What is your preferred date for the appointment?',
        'What time works best for you?',
        'What is your contact information?',
        'Do you have any special requirements?'
      ],
      firstMessage: 'Hello! I\'m calling to help you schedule an appointment. When would be a convenient time for you?'
    },
    'lead_qualification': {
      name: 'Lead Qualification Agent',
      purpose: 'Qualify potential leads',
      questions: [
        'What is your company name and role?',
        'What is your current budget range?',
        'When are you looking to make a decision?',
        'What are your main pain points?'
      ],
      firstMessage: 'Hello! I\'m calling to learn more about your business needs and see how we might be able to help.'
    },
    'feedback_collection': {
      name: 'Feedback Collection Agent',
      purpose: 'Collect product feedback',
      questions: [
        'How long have you been using our product?',
        'What features do you use most?',
        'What challenges have you encountered?',
        'What new features would you like to see?'
      ],
      firstMessage: 'Hello! I\'m calling to get your valuable feedback on our product. Your insights help us improve!'
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
        setCallStatus(`✅ Call initiated successfully! Batch Call ID: ${data.batch_call_id}`)
        setLastCallId(data.batch_call_id)
      } else {
        setCallStatus(`❌ Call failed: ${data.error}`)
      }
    } catch (error) {
      setCallStatus('❌ Error making call')
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

  return (
    <div className="App">
      <header className="App-header">
        <h1>Careexpand Protocol AI</h1>
        <p>Configure Protocl CEX AI agent</p>
      </header>

      <main className="main-content">
        {/* Agent Configuration Section */}
        <section className="config-section">
          <h2>🎯 Agent Configuration</h2>
          
          {/* Quick Templates */}
          <div className="templates">
            <h3>Quick Templates:</h3>
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
                <input
                  type="text"
                  value={question}
                  onChange={(e) => updateQuestion(index, e.target.value)}
                  placeholder={`Question ${index + 1}`}
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
        </section>

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
