import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import openai
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WhatsAppAIAgent:
    def __init__(self, openai_api_key, headless=False):
        """
        Initialize the WhatsApp AI Agent
        
        Args:
            openai_api_key (str): Your OpenAI API key
            headless (bool): Whether to run browser in headless mode
        """
        self.openai_api_key = openai_api_key
        openai.api_key = openai_api_key
        self.driver = None
        self.processed_messages = set()
        self.headless = headless
        
        # Conversation context storage
        self.conversation_contexts = {}
        
        # Auto-reply settings
        self.auto_reply_enabled = True
        self.response_delay = 2  # seconds to wait before responding
        
        # Blacklist/whitelist for contacts
        self.blacklisted_contacts = set()
        self.whitelisted_contacts = set()  # if not empty, only these contacts get replies
        
    def setup_driver(self):
        """Setup Chrome WebDriver for WhatsApp Web"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Keep session data to avoid re-scanning QR code
        chrome_options.add_argument("--user-data-dir=./whatsapp_session")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.get("https://web.whatsapp.com")
        
    def wait_for_qr_scan(self):
        """Wait for user to scan QR code and login"""
        logger.info("Please scan the QR code to login to WhatsApp Web")
        try:
            # Wait for the main chat interface to load
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="chat-list"]'))
            )
            logger.info("Successfully logged into WhatsApp Web")
            return True
        except Exception as e:
            logger.error(f"Failed to login: {e}")
            return False
    
    def generate_ai_response(self, message_text, sender_name):
        """Generate AI response using OpenAI"""
        try:
            # Get conversation context
            context = self.conversation_contexts.get(sender_name, [])
            
            # Build conversation history for context
            conversation_history = ""
            for msg in context[-5:]:  # Last 5 messages for context
                conversation_history += f"{msg['sender']}: {msg['message']}\n"
            
            # Create prompt for AI
            prompt = f"""You are an AI assistant responding to WhatsApp messages on behalf of your user. 
            
Conversation history with {sender_name}:
{conversation_history}

New message from {sender_name}: {message_text}

Please respond naturally and helpfully. Keep responses concise and conversational, suitable for WhatsApp. 
If the message requires urgent attention or is very important, suggest they call or mention you'll get back to them soon.
Don't mention that you're an AI unless directly asked."""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant responding to WhatsApp messages."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Update conversation context
            if sender_name not in self.conversation_contexts:
                self.conversation_contexts[sender_name] = []
            
            self.conversation_contexts[sender_name].append({
                'sender': sender_name,
                'message': message_text,
                'timestamp': datetime.now().isoformat()
            })
            
            self.conversation_contexts[sender_name].append({
                'sender': 'AI Assistant',
                'message': ai_response,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 10 messages per contact
            if len(self.conversation_contexts[sender_name]) > 10:
                self.conversation_contexts[sender_name] = self.conversation_contexts[sender_name][-10:]
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "Thanks for your message! I'll get back to you soon."
    
    def should_respond_to_contact(self, contact_name):
        """Check if we should respond to this contact"""
        if contact_name in self.blacklisted_contacts:
            return False
        
        if self.whitelisted_contacts and contact_name not in self.whitelisted_contacts:
            return False
        
        return True
    
    def get_unread_messages(self):
        """Get all unread messages from WhatsApp"""
        try:
            # Find all unread chats (those with notification badges)
            unread_chats = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="chat-list"] [role="listitem"]:has([data-testid="icon-unread"])')
            
            new_messages = []
            
            for chat in unread_chats:
                try:
                    # Click on the chat
                    chat.click()
                    time.sleep(1)
                    
                    # Get contact name
                    contact_name_element = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="conversation-header"] ._ao3e')
                    contact_name = contact_name_element.text
                    
                    # Get all messages in the chat
                    messages = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="msg-container"]')
                    
                    # Find unread messages (typically the last few)
                    for message in messages[-5:]:  # Check last 5 messages
                        try:
                            # Check if message is incoming (not sent by us)
                            is_outgoing = message.find_elements(By.CSS_SELECTOR, '[data-testid="msg-meta"] [data-testid="msg-check"]')
                            if is_outgoing:
                                continue
                                
                            # Get message text
                            message_text_element = message.find_element(By.CSS_SELECTOR, '[data-testid="conversation-compose-box-input"]')
                            message_text = message_text_element.text
                            
                            # Create unique message ID
                            message_id = f"{contact_name}_{hash(message_text)}_{len(message_text)}"
                            
                            if message_id not in self.processed_messages and message_text.strip():
                                new_messages.append({
                                    'id': message_id,
                                    'contact': contact_name,
                                    'message': message_text,
                                    'timestamp': datetime.now()
                                })
                                self.processed_messages.add(message_id)
                                
                        except Exception as e:
                            logger.debug(f"Error processing individual message: {e}")
                            continue
                            
                except Exception as e:
                    logger.error(f"Error processing chat: {e}")
                    continue
            
            return new_messages
            
        except Exception as e:
            logger.error(f"Error getting unread messages: {e}")
            return []
    
    def send_message(self, message_text):
        """Send a message in the currently open chat"""
        try:
            # Find the message input box
            input_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="conversation-compose-box-input"]'))
            )
            
            # Clear and type the message
            input_box.clear()
            input_box.send_keys(message_text)
            
            # Find and click send button
            send_button = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="send"]')
            send_button.click()
            
            logger.info(f"Sent message: {message_text[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def process_messages(self):
        """Main loop to process and respond to messages"""
        logger.info("Starting message processing loop...")
        
        while True:
            try:
                if not self.auto_reply_enabled:
                    time.sleep(5)
                    continue
                
                # Get unread messages
                new_messages = self.get_unread_messages()
                
                for msg in new_messages:
                    contact_name = msg['contact']
                    message_text = msg['message']
                    
                    logger.info(f"New message from {contact_name}: {message_text[:50]}...")
                    
                    # Check if we should respond to this contact
                    if not self.should_respond_to_contact(contact_name):
                        logger.info(f"Skipping response to {contact_name} (blacklisted or not whitelisted)")
                        continue
                    
                    # Generate AI response
                    ai_response = self.generate_ai_response(message_text, contact_name)
                    
                    # Wait a bit to seem more natural
                    time.sleep(self.response_delay)
                    
                    # Send the response
                    if self.send_message(ai_response):
                        logger.info(f"Responded to {contact_name}: {ai_response[:50]}...")
                    else:
                        logger.error(f"Failed to send response to {contact_name}")
                
                # Wait before checking for new messages again
                time.sleep(5)
                
            except KeyboardInterrupt:
                logger.info("Stopping message processing...")
                break
            except Exception as e:
                logger.error(f"Error in message processing loop: {e}")
                time.sleep(10)  # Wait longer on error
    
    def add_to_blacklist(self, contact_name):
        """Add a contact to blacklist"""
        self.blacklisted_contacts.add(contact_name)
        logger.info(f"Added {contact_name} to blacklist")
    
    def add_to_whitelist(self, contact_name):
        """Add a contact to whitelist"""
        self.whitelisted_contacts.add(contact_name)
        logger.info(f"Added {contact_name} to whitelist")
    
    def toggle_auto_reply(self):
        """Toggle auto-reply on/off"""
        self.auto_reply_enabled = not self.auto_reply_enabled
        status = "enabled" if self.auto_reply_enabled else "disabled"
        logger.info(f"Auto-reply {status}")
    
    def start(self):
        """Start the WhatsApp AI agent"""
        try:
            logger.info("Starting WhatsApp AI Agent...")
            
            # Setup browser
            self.setup_driver()
            
            # Wait for QR scan and login
            if not self.wait_for_qr_scan():
                logger.error("Failed to login to WhatsApp Web")
                return
            
            # Start processing messages
            self.process_messages()
            
        except Exception as e:
            logger.error(f"Error starting agent: {e}")
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """Main function to run the WhatsApp AI Agent"""
    
    # Configuration
    OPENAI_API_KEY = "your-openai-api-key-here"  # Replace with your OpenAI API key
    
    # Create and start the agent
    agent = WhatsAppAIAgent(
        openai_api_key=OPENAI_API_KEY,
        headless=False  # Set to True to run without GUI
    )
    
    # Optional: Configure contacts
    # agent.add_to_whitelist("John Doe")  # Only respond to these contacts
    # agent.add_to_blacklist("Spam Contact")  # Never respond to these
    
    # Start the agent
    agent.start()

if __name__ == "__main__":
    main()
