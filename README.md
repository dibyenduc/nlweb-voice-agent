# NLWeb Voice Agent 🎤

A voice-enabled extension for Microsoft's NLWeb semantic search system that allows users to interact with podcast databases through natural speech commands.

## Overview

This project enhances the original [NLWeb](https://github.com/nlweb-ai/NLWeb) open-source semantic search platform by adding comprehensive voice interaction capabilities. Users can now speak their queries naturally and receive audio responses about podcast episodes from "Behind the Tech" and "Decoder" podcast collections.

## My Contributions

I built a complete voice interface layer on top of the existing NLWeb API, adding:

- **Speech Recognition**: Real-time voice input processing using Google Speech Recognition with offline fallback
- **Text-to-Speech**: Natural voice responses using pyttsx3 with optimized speech parameters
- **Intelligent Response Processing**: Advanced SSE (Server-Sent Events) stream parsing that handles complex API responses
- **Robust Error Handling**: Fallback mechanisms for network timeouts, speech recognition failures, and API issues
- **Interactive Voice Loop**: Continuous conversation mode with natural exit commands
- **Response Optimization**: Voice-friendly content formatting with appropriate length limits and cleanup
- **Comprehensive Logging**: Detailed emoji-enhanced logging for debugging and monitoring

## How to Run It

### Prerequisites

1. **NLWeb Backend**: First, set up and run the original NLWeb system following the [NLWeb Hello World guide](https://github.com/nlweb-ai/NLWeb/blob/main/docs/nlweb-hello-world.md)

2. **Python Dependencies**: Install the required voice processing libraries:
```bash
pip install speechrecognition pyttsx3 requests
```

3. **System Requirements**:
   - Microphone access for speech input
   - Audio output for TTS responses
   - Internet connection for Google Speech Recognition (with offline fallback)

### Running the Voice Agent

1. **Start NLWeb Backend** (in separate terminal):
```bash
# Follow NLWeb documentation to start the backend service on localhost:8000
```

2. **Launch Voice Agent**:
```bash
python working_voice_agent.py
```

3. **Voice Commands**: Speak naturally after hearing the initialization message:
   - "What podcasts do you have?"
   - "Tell me about Microsoft"
   - "Find episodes about machine learning"
   - Say "goodbye", "quit", "stop", or "exit" to end

### Test Modes

Run automated tests without voice interaction:

```bash
# Quick test
python working_voice_agent.py test quick

# Full test suite
python working_voice_agent.py test full

# Debug mode
python working_voice_agent.py test debug
```

## Demo Output

```
[INFO] 🔧 Initializing NLWeb Voice Agent...
[INFO] 🎤 Setting up speech recognition...
[INFO] 🔊 Setting up text-to-speech...
[INFO] ✅ NLWeb Voice Agent initialized.
[INFO] 🚀 Starting interactive voice mode...

[Speaking] "Hello! I'm your podcast voice assistant..."

[INFO] 🎤 Listening... (speak clearly)
[INFO] 📝 Heard: 'Microsoft'
[INFO] ❓ Asking NLWeb: 'Microsoft'
[INFO] 📊 Found 50 relevant documents.
[INFO] ✅ Generated response from 3 recommendations

[Speaking] "Here are relevant podcast episodes: 
1. Lisa Su, Chair and CEO, AMD 
2. Xyla Foxlin, Engineer and YouTube Creator 
3. William A. Adams, Software Engineer, DEI Innovator, and Philanthropist"
```

## Architecture

The voice agent operates as a client to the NLWeb API, providing:

- **Speech Input Layer**: Captures and processes voice commands
- **API Integration**: Communicates with NLWeb backend via REST API
- **Response Processing**: Parses streaming SSE responses and extracts recommendations  
- **Audio Output**: Converts text responses to natural speech
- **Error Recovery**: Handles various failure scenarios gracefully

## Original Project

This project builds upon [Microsoft's NLWeb](https://github.com/nlweb-ai/NLWeb), an open-source semantic search platform for enterprise knowledge bases. NLWeb provides the core semantic search capabilities, while this voice agent adds an intuitive spoken interface.

## Features

- 🎙️ **Natural Speech Recognition**: Speak queries in plain English
- 🔊 **Audio Responses**: Hear results read aloud with natural voice synthesis
- 🔄 **Continuous Interaction**: Maintains conversation context throughout session
- 🛡️ **Robust Fallbacks**: Multiple error recovery mechanisms
- 📊 **Rich Logging**: Comprehensive status tracking with visual indicators
- ⚡ **Multiple Modes**: Interactive voice mode and automated testing
- 🎯 **Smart Filtering**: Optimized for voice-friendly response lengths

## License

This voice extension maintains compatibility with the original NLWeb project's licensing terms.