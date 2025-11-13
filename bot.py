from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
import logging
import time
import random
import json
import os
from datetime import datetime, timedelta
from flask import Flask, jsonify
import threading
from waitress import serve
import uuid

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

USERNAME = os.getenv('INSTAGRAM_USERNAME')
PASSWORD = os.getenv('INSTAGRAM_PASSWORD')

class GrowthAnalytics:
    def __init__(self):
        self.analytics_file = "growth_analytics.json"
        self.load_analytics()
    
    def load_analytics(self):
        try:
            with open(self.analytics_file, 'r') as f:
                self.data = json.load(f)
        except:
            self.data = {
                "bot_status": "initializing",
                "login_attempts": 0,
                "last_login": None,
                "last_error": None,
                "total_sessions": 0,
                "created_at": datetime.now().isoformat()
            }
    
    def save_analytics(self):
        with open(self.analytics_file, 'w') as f:
            json.dump(self.data, f, indent=2)

class SmartInstagramBot:
    def __init__(self):
        self.cl = Client()
        self.analytics = GrowthAnalytics()
        self.bot_status = "initializing"
        self.last_error = None
        
    def setup_client_advanced(self):
        """Configuration avancée pour éviter la détection"""
        try:
            # User agents alternatifs
            user_agents = [
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (Linux; Android 13; SM-S901U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36"
            ]
            
            settings = {
                "user_agent": random.choice(user_agents),
                "device_settings": {
                    "app_version": "320.0.0.0.0",
                    "android_version": 33,
                    "android_release": "13.0",
                    "dpi": "480dpi",
                    "resolution": "1080x2400",
                    "manufacturer": "Samsung",
                    "device": "SM-S901U",
                    "model": "SM-S901U",
                },
                "country": "FR",
                "locale": "fr_FR",
                "timezone_offset": 3600,
                "uuid": self.generate_uuid(),
            }
            
            self.cl.set_settings(settings)
            self.cl.delay_range = [15, 30]
            self.cl.request_timeout = 30
            return True
        except Exception as e:
            logger.error(f"❌ Erreur configuration: {e}")
            return False
    
    def generate_uuid(self):
        """Générer un UUID unique"""
        return str(uuid.uuid4())
    
    def manual_login_flow(self):
        """Flux de connexion manuel pour contourner CSRF"""
        try:
            logger.info("🔄 Tentative de connexion manuelle...")
            
            # Supprimer toute session existante
            if os.path.exists("session.json"):
                os.remove("session.json")
            
            # Réinitialiser le client avec nouvelle configuration
            self.cl = Client()
            if not self.setup_client_advanced():
                return False
            
            # Délai important avant connexion
            logger.info("⏳ Préparation de la connexion...")
            time.sleep(10)
            
            # Tentative de connexion
            logger.info(f"🔐 Connexion pour {USERNAME}...")
            login_result = self.cl.login(USERNAME, PASSWORD)
            
            if login_result:
                logger.info("✅ Connexion réussie!")
                # Sauvegarder la session
                self.cl.dump_settings("session.json")
                return True
            else:
                logger.error("❌ Échec de la connexion")
                return False
                
        except ChallengeRequired as e:
            logger.error("🔐 Challenge Instagram requis - Connecte-toi manuellement sur ton compte")
            self.last_error = "Challenge de sécurité requis - Vérifie ton compte Instagram"
            return False
        except Exception as e:
            logger.error(f"💥 Erreur connexion: {str(e)}")
            self.last_error = str(e)
            return False
    
    def safe_login(self):
        """Connexion sécurisée"""
        try:
            logger.info("🔐 Processus de connexion...")
            self.bot_status = "logging_in"
            self.analytics.data["login_attempts"] += 1
            self.analytics.save_analytics()
            
            # Essayer d'abord avec une session existante
            if os.path.exists("session.json"):
                try:
                    self.cl.load_settings("session.json")
                    user_info = self.cl.account_info()
                    logger.info(f"✅ Session valide: {user_info.username}")
                    self.bot_status = "connected"
                    self.analytics.data["last_login"] = datetime.now().isoformat()
                    self.analytics.save_analytics()
                    return True
                except Exception as e:
                    logger.warning(f"🔄 Session expirée: {e}")
                    if os.path.exists("session.json"):
                        os.remove("session.json")
            
            # Connexion manuelle
            if self.manual_login_flow():
                self.bot_status = "connected"
                self.analytics.data["last_login"] = datetime.now().isoformat()
                self.analytics.save_analytics()
                return True
            else:
                self.bot_status = "login_failed"
                return False
                
        except Exception as e:
            error_msg = f"Erreur générale: {str(e)}"
            logger.error(f"💥 {error_msg}")
            self.last_error = error_msg
            self.bot_status = "error"
            return False
    
    def get_bot_info(self):
        """Récupérer les infos du bot"""
        return {
            "status": self.bot_status,
            "login_attempts": self.analytics.data["login_attempts"],
            "last_login": self.analytics.data["last_login"],
            "last_error": self.last_error,
            "timestamp": datetime.now().isoformat(),
            "username": USERNAME if USERNAME else "non_configuré",
            "message": "Instagram Growth Bot"
        }

# Instance globale du bot
bot_instance = None

def run_bot():
    """Fonction principale du bot"""
    global bot_instance
    logger.info("🚀 Démarrage du Bot Instagram Growth")
    
    if not USERNAME or not PASSWORD:
        logger.error("❌ Variables d'environnement manquantes")
        return
    
    bot_instance = SmartInstagramBot()
    
    # Tentative de connexion
    if bot_instance.safe_login():
        logger.info("✅ Bot connecté avec succès!")
        # Simulation d'activité
        while True:
            try:
                # Vérifier la connexion périodiquement
                if bot_instance.bot_status == "connected":
                    user_info = bot_instance.cl.account_info()
                    logger.info(f"🤖 Bot actif - Followers: {user_info.follower_count}")
                
                time.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.warning("🔄 Reconnexion nécessaire...")
                bot_instance.safe_login()
                time.sleep(60)
    else:
        logger.error("❌ Échec de la connexion")
        logger.info("💡 Conseil: Connecte-toi manuellement à Instagram puis réessaie")

# Application Flask
app = Flask(__name__)

@app.route('/')
def home():
    """Page d'accueil"""
    if bot_instance is None:
        return """
        <html>
            <head><title>Instagram Bot</title></head>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h1>🤖 Bot Instagram Growth</h1>
                <div style="background: #f0f8ff; padding: 20px; border-radius: 10px;">
                    <h2>Status: Initialisation...</h2>
                    <p>Le bot démarre...</p>
                </div>
            </body>
        </html>
        """
    
    info = bot_instance.get_bot_info()
    status_color = {
        "connected": "#d4edda",
        "error": "#f8d7da", 
        "login_failed": "#fff3cd",
        "challenge_required": "#ffeaa7"
    }.get(info['status'], '#e2e3e5')
    
    return f"""
    <html>
        <head><title>Instagram Bot Status</title></head>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h1>🤖 Bot Instagram Growth</h1>
            <div style="background: {status_color}; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h2>Status: {info['status'].upper()}</h2>
                <p><strong>Utilisateur:</strong> {info['username']}</p>
                <p><strong>Dernière activité:</strong> {info['timestamp']}</p>
                <p><strong>Tentatives:</strong> {info['login_attempts']}</p>
                <p><strong>Dernière connexion:</strong> {info['last_login'] or 'Jamais'}</p>
                <p><strong>Erreur:</strong> {info['last_error'] or 'Aucune'}</p>
            </div>
            <p><a href="/health">Health Check</a> | <a href="/status">Status API</a></p>
            <div style="margin-top: 20px; padding: 15px; background: #e7f3ff; border-radius: 5px;">
                <h3>💡 Conseils de dépannage:</h3>
                <ul>
                    <li>Vérifie que ton compte Instagram est actif</li>
                    <li>Connecte-toi manuellement d'abord</li>
                    <li>Accepte les éventuels challenges de sécurité</li>
                    <li>Réessaie dans quelques minutes</li>
                </ul>
            </div>
        </body>
    </html>
    """

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/status')
def status():
    if bot_instance is None:
        return jsonify({"status": "not_initialized"})
    return jsonify(bot_instance.get_bot_info())

@app.route('/reconnect')
def reconnect():
    if bot_instance:
        bot_instance.safe_login()
        return jsonify({"reconnect_attempted": True, "new_status": bot_instance.bot_status})
    return jsonify({"error": "Bot non initialisé"})

def start_server():
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🌐 Serveur démarré sur le port {port}")
    serve(app, host='0.0.0.0', port=port)

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    start_server()
