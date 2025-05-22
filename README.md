# WhatsApp AI Auto-Reply Agent

An intelligent AI-powered bot that automatically responds to WhatsApp messages on your behalf using OpenAI's GPT model. The agent monitors WhatsApp Web for incoming messages and generates contextual, natural responses.

## Important Disclaimer

**Use at your own risk.** This tool may violate WhatsApp's Terms of Service. WhatsApp prohibits automated messaging and could potentially ban your account. Consider the risks before using this in production.

## Features

- **Automatic Message Detection**: Continuously monitors WhatsApp Web for new messages
- **AI-Powered Responses**: Uses OpenAI GPT-3.5-turbo for natural, contextual replies
- **Conversation Context**: Maintains chat history for better response quality
- **Contact Management**: Blacklist/whitelist functionality to control interactions
- **Session Persistence**: Saves login session to avoid repeated QR code scanning
- **Customizable Delays**: Natural response timing to avoid detection
- **Headless Mode**: Option to run without browser GUI
- **Comprehensive Logging**: Detailed logs for monitoring and debugging

## Prerequisites

- Python 3.7 or higher
- Google Chrome browser
- ChromeDriver (compatible with your Chrome version)
- OpenAI API key
- WhatsApp account

## Installation

1. **Clone or download the script**
```bash
git clone https://github.com/CodeDestroyer19/ai-whatsapp-agent
cd whatsapp-ai-agent
```

2. **Install required Python packages**
```bash
pip install selenium openai webdriver-manager
```

3. **Install ChromeDriver**

   **Option A: Automatic (Recommended)**
   ```bash
   pip install webdriver-manager
   ```
   Then modify the script to use WebDriverManager:
   ```python
   from webdriver_manager.chrome import ChromeDriverManager
   from selenium.webdriver.chrome.service import Service
   
   # In setup_driver method:
   service = Service(ChromeDriverManager().install())
   self.driver = webdriver.Chrome(service=service, options=chrome_options)
   ```

   **Option B: Manual**
   - Download ChromeDriver from https://chromedriver.chromium.org/
   - Add ChromeDriver to your system PATH

## Configuration

1. **Get OpenAI API Key**
   - Visit https://platform.openai.com/api-keys
   - Create a new API key
   - Replace `"your-openai-api-key-here"` in the script

2. **Configure Settings** (Optional)
   ```python
   # In main() function:
   agent = WhatsAppAIAgent(
       openai_api_key=OPENAI_API_KEY,
       headless=False  # Set True for no GUI
   )
   
   # Optional contact filtering:
   agent.add_to_whitelist("John Doe")  # Only these contacts get replies
   agent.add_to_blacklist("Spam Bot")  # These contacts are ignored
   
   # Adjust response settings:
   agent.response_delay = 3  # Seconds to wait before responding
   ```

## Usage

### Basic Usage

1. **Run the agent**
   ```bash
   python whatsapp_agent.py
   ```

2. **First-time setup**
   - Chrome browser will open with WhatsApp Web
   - Scan the QR code with your phone's WhatsApp
   - Wait for "Successfully logged into WhatsApp Web" message

3. **Let it run**
   - The agent will now monitor for new messages
   - Responses are generated automatically
   - Check console logs for activity

### Advanced Usage

#### Contact Management
```python
# Only respond to specific contacts
agent.add_to_whitelist("Boss")
agent.add_to_whitelist("Family Group")

# Never respond to certain contacts
agent.add_to_blacklist("Marketing Bot")
agent.add_to_blacklist("Spam Account")
```

#### Customizing AI Responses
Modify the prompt in `generate_ai_response()` method:
```python
prompt = f"""You are a professional assistant responding to WhatsApp messages.

Context: Working hours are 9 AM - 6 PM EST.
Current message from {sender_name}: {message_text}

Respond professionally and briefly. If it's after hours, mention you'll respond during business hours."""
```

#### Running in Background (Headless)
```python
agent = WhatsAppAIAgent(
    openai_api_key=OPENAI_API_KEY,
    headless=True  # No browser window
)
```

#### Toggling Auto-Reply
```python
# Disable auto-replies temporarily
agent.toggle_auto_reply()  # Turns off
agent.toggle_auto_reply()  # Turns back on
```

## Monitoring and Logs

The agent provides detailed logging:

```bash
2024-01-20 10:30:15 - INFO - Starting WhatsApp AI Agent...
2024-01-20 10:30:20 - INFO - Please scan the QR code to login
2024-01-20 10:30:45 - INFO - Successfully logged into WhatsApp Web
2024-01-20 10:31:00 - INFO - Starting message processing loop...
2024-01-20 10:31:30 - INFO - New message from John Doe: Hey, are you available?
2024-01-20 10:31:33 - INFO - Responded to John Doe: Hi! Yes, I'm here. How can I help you?
```

## Troubleshooting

### Common Issues

1. **ChromeDriver not found**
   ```
   Error: 'chromedriver' executable needs to be in PATH
   ```
   **Solution**: Install webdriver-manager or manually add ChromeDriver to PATH

2. **OpenAI API errors**
   ```
   Error: Invalid API key provided
   ```
   **Solution**: Verify your OpenAI API key is correct and has credits

3. **WhatsApp Web login issues**
   ```
   Error: Failed to login: Message: no such element
   ```
   **Solution**: Make sure WhatsApp Web loads properly, try clearing browser data

4. **Messages not detected**
   ```
   No new messages found but there are unread chats
   ```
   **Solution**: WhatsApp's HTML structure may have changed, update CSS selectors

### Debug Mode

Enable verbose logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

### Session Issues

If QR code keeps appearing:
```bash
# Clear saved session
rm -rf ./whatsapp_session
```

## Performance Tips

1. **Optimize Response Time**
   - Reduce `response_delay` for faster replies
   - Use `headless=True` for better performance

2. **Manage Memory Usage**
   - Conversation contexts are limited to 10 messages per contact
   - Restart agent periodically for long-running instances

3. **API Cost Management**
   - Monitor OpenAI usage dashboard
   - Consider using shorter prompts
   - Implement daily/monthly limits

## Security Considerations

1. **API Key Security**
   - Store API key in environment variables
   - Never commit API keys to version control

2. **Privacy**
   - All messages are sent to OpenAI for processing
   - Consider data sensitivity before enabling

3. **Account Safety**
   - Use delays between messages
   - Monitor for unusual account activity
   - Have backup communication methods

## Customization Examples

### Business Hours Bot
```python
def generate_business_response(self, message_text, sender_name):
    current_hour = datetime.now().hour
    if 9 <= current_hour <= 17:  # Business hours
        return self.generate_ai_response(message_text, sender_name)
    else:
        return "Thanks for your message! I'll respond during business hours (9 AM - 6 PM)."
```

### Keyword-Based Responses
```python
def get_quick_response(self, message_text):
    message_lower = message_text.lower()
    if any(word in message_lower for word in ['urgent', 'emergency', 'asap']):
        return "I see this is urgent. Let me get back to you immediately."
    elif any(word in message_lower for word in ['thanks', 'thank you']):
        return "You're welcome! 😊"
    return None  # Use AI for other messages
```

### Meeting Scheduler Integration
```python
def check_calendar_availability(self, message_text):
    if 'meeting' in message_text.lower() or 'schedule' in message_text.lower():
        # Integrate with Google Calendar API
        return "Let me check my calendar availability..."
    return None
```

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the agent.

## License

This project is for educational purposes. Use responsibly and in accordance with WhatsApp's Terms of Service.

## Support

If you encounter issues:
1. Check the troubleshooting section
2. Review the logs for error details
3. Ensure all dependencies are properly installed
4. Verify WhatsApp Web accessibility in your region

---

**Remember**: This tool is experimental. Always test thoroughly before relying on it for important communications.
