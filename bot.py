from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
import logging
import time
import random
import os
from datetime import datetime
from flask import Flask, jsonify
import threading
from waitress import serve

# Désactiver les logs verbeux
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

USERNAME = os.getenv('INSTAGRAM_USERNAME')
PASSWORD = os.getenv('INSTAGRAM_PASSWORD')

class SimpleInstagramBot:
    def __init__(self):
        self.client = Client()
        self.status = "initializing"
        self.last_error = None
        
    def setup_simple_client(self):
        """Configuration minimaliste"""
        try:
            # Settings très basiques
            settings = {
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
            }
            self.client.set_settings(settings)
            self.client.delay_range = [20, 40]  # Délais très longs
            return True
        except Exception as e:
            logger.error(f"Configuration error: {e}")
            return False
    
    def simple_login(self):
        """Connexion simple et directe"""
        try:
            logger.info("Attempting simple login...")
            self.status = "logging_in"
            
            # Essayer la session existante d'abord
            if os.path.exists("session.json"):
                try:
                    self.client.load_settings("session.json")
                    user = self.client.account_info()
                    logger.info(f"Session valid for: {user.username}")
                    self.status = "connected"
                    return True
                except:
                    os.remove("session.json")
            
            # Configuration minimaliste
            self.setup_simple_client()
            
            # Délai important
            time.sleep(random.randint(15, 30))
            
            # Connexion directe
            if self.client.login(USERNAME, PASSWORD):
                self.client.dump_settings("session.json")
                self.status = "connected"
                logger.info("Login successful!")
                return True
            else:
                self.status = "login_failed"
                return False
                
        except ChallengeRequired:
            self.last_error = "Instagram security challenge required - Please login manually first"
            self.status = "challenge_required"
            return False
        except Exception as e:
            self.last_error = str(e)
            self.status = "error"
            return False

# Instance globale
instagram_bot = None

def run_simple_bot():
    global instagram_bot
    logger.info("Starting Simple Instagram Bot")
    
    if not USERNAME or not PASSWORD:
        logger.error("Missing credentials")
        return
    
    instagram_bot = SimpleInstagramBot()
    
    # Tentative de connexion
    if instagram_bot.simple_login():
        logger.info("Bot successfully connected!")
        # Maintenir la connexion
        while True:
            try:
                time.sleep(300)
                # Vérifier connexion
                instagram_bot.client.account_info()
            except:
                logger.warning("Reconnecting...")
                instagram_bot.simple_login()
    else:
        logger.error("Failed to connect bot")

# Application web
app = Flask(__name__)

@app.route('/')
def home():
    if instagram_bot is None:
        return """
        <html>
        <head><title>Instagram Bot</title></head>
        <body style="font-family: Arial; padding: 20px;">
            <h1>🤖 Instagram Bot</h1>
            <div style="background: #e7f3ff; padding: 20px; border-radius: 10px;">
                <h2>Status: Initializing...</h2>
                <p>The bot is starting up.</p>
            </div>
        </body>
        </html>
        """
    
    status_info = {
        "status": instagram_bot.status,
        "last_error": instagram_bot.last_error,
        "timestamp": datetime.now().isoformat(),
        "username": USERNAME
    }
    
    return f"""
    <html>
    <head><title>Instagram Bot Status</title></head>
    <body style="font-family: Arial; padding: 20px;">
        <h1>🤖 Instagram Bot Status</h1>
        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px;">
            <h2>Status: {status_info['status']}</h2>
            <p><strong>User:</strong> {status_info['username']}</p>
            <p><strong>Last Error:</strong> {status_info['last_error'] or 'None'}</p>
            <p><strong>Time:</strong> {status_info['timestamp']}</p>
        </div>
        
        <div style="margin-top: 20px; padding: 15px; background: #fff3cd; border-radius: 5px;">
            <h3>🔧 Troubleshooting CSRF Error:</h3>
            <ol>
                <li>Go to <a href="https://instagram.com" target="_blank">instagram.com</a></li>
                <li>Login with <strong>{USERNAME}</strong></li>
                <li>Complete any security challenges</li>
                <li>Wait 10 minutes</li>
                <li><a href="/reconnect">Click here to reconnect</a></li>
            </ol>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "instagram-bot"})

@app.route('/reconnect')
def reconnect():
    if instagram_bot:
        instagram_bot.simple_login()
        return jsonify({"reconnect_attempted": True})
    return jsonify({"error": "Bot not initialized"})

def start_web_server():
    port = int(os.environ.get("PORT", 8080))
    serve(app, host='0.0.0.0', port=port)

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_simple_bot, daemon=True)
    bot_thread.start()
    start_web_server()
