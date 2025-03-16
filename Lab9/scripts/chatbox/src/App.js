import React, { useState } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [processing, setProcessing] = useState(false);
  const [uploading, setUploading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMessage = { sender: 'user', text: input };
    setMessages(prev => [...prev, userMessage]);
    setProcessing(true);

    try {
      const response = await fetch('http://127.0.0.1:5000/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: input })
      });
      const data = await response.json();
      const botMessage = { sender: 'bot', text: data.answer || "No answer returned: Please process PDFs first." };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error("Error calling backend:", error);
      setMessages(prev => [...prev, { sender: 'bot', text: "Error getting response" }]);
    }
    setInput("");
    setProcessing(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileUpload = async (e) => {
    const files = e.target.files;
    if (files.length === 0) return;

    setUploading(true);
    const formData = new FormData();
    for (let file of files) {
      formData.append('pdfs', file);
    }
    try {
      const response = await fetch('http://127.0.0.1:5000/process', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();
      console.log("Process response:", data);
      alert(data.message || "PDF processed successfully.");
    } catch (error) {
      console.error("Error processing PDF:", error);
      alert("Error processing PDF");
    }
    setUploading(false);
  };

  return (
    <div className="App">
      <div className="chat-wrapper">
        <div className="chat-header">Qroup 4 LLM Chatbox</div>
        <div className="chat-content">
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.sender === 'user' ? 'user-message' : 'bot-message'}`}>
              {msg.text}
            </div>
          ))}
          {processing && <div className="processing-indicator">Processing...</div>}
        </div>
        <div className="chat-input-area">
          <label className="file-upload">
            Upload PDF
            <input type="file" accept="application/pdf" multiple onChange={handleFileUpload} />
          </label>
          {uploading && <div className="uploading-indicator">Uploading...</div>}
          <textarea
            className="chat-input"
            placeholder="Type your question..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
          />
          <button className="send-button" onClick={handleSend} disabled={processing || uploading}>
            {processing ? "Processing..." : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
