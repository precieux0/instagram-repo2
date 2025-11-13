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
from waitress import serve  # Serveur production pour Windows

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
        
    def setup_client(self):
        """Configuration du client avec des paramètres réalistes"""
        try:
            # Settings pour éviter la détection
            settings = {
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
                "device_settings": {
                    "app_version": "320.0.0.0.0",
                    "android_version": 34,
                    "android_release": "14.0",
                    "dpi": "480dpi",
                    "resolution": "1080x2400",
                    "manufacturer": "Samsung",
                    "device": "SM-S901U",
                    "model": "SM-S901U",
                },
                "country": "US",
                "locale": "en_US",
                "timezone_offset": -28800
            }
            self.cl.set_settings(settings)
            self.cl.delay_range = [10, 20]
            return True
        except Exception as e:
            logger.error(f"❌ Erreur configuration client: {e}")
            return False
    
    def safe_login(self):
        """Connexion sécurisée avec gestion améliorée"""
        try:
            logger.info("🔐 Tentative de connexion...")
            self.bot_status = "logging_in"
            self.analytics.data["login_attempts"] += 1
            self.analytics.save_analytics()
            
            # Configuration initiale
            if not self.setup_client():
                return False
            
            # Supprimer session existante problématique
            if os.path.exists("session.json"):
                try:
                    self.cl.load_settings("session.json")
                    # Tester la session
                    user_info = self.cl.account_info()
                    logger.info(f"✅ Session valide pour: {user_info.username}")
                    self.bot_status = "connected"
                    self.analytics.data["last_login"] = datetime.now().isoformat()
                    self.analytics.save_analytics()
                    return True
                except Exception as e:
                    logger.warning(f"🔄 Session invalide: {e}")
                    if os.path.exists("session.json"):
                        os.remove("session.json")
            
            # Nouvelle connexion
            logger.info("🔄 Connexion avec identifiants...")
            time.sleep(random.randint(8, 15))
            
            if USERNAME and PASSWORD:
                login_result = self.cl.login(USERNAME, PASSWORD)
                if login_result:
                    logger.info("✅ Connexion réussie!")
                    self.cl.dump_settings("session.json")
                    self.bot_status = "connected"
                    self.analytics.data["last_login"] = datetime.now().isoformat()
                    self.analytics.save_analytics()
                    return True
            
            logger.error("❌ Échec de la connexion")
            self.bot_status = "login_failed"
            return False
            
        except ChallengeRequired as e:
            error_msg = "Challenge de sécurité Instagram requis - Connecte-toi manuellement sur ton compte"
            logger.error(f"🔐 {error_msg}")
            self.last_error = error_msg
            self.bot_status = "challenge_required"
            return False
        except Exception as e:
            error_msg = str(e)
            logger.error(f"💥 Erreur de connexion: {error_msg}")
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
            "username_set": bool(USERNAME),
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
        logger.info("💡 Configure INSTAGRAM_USERNAME et INSTAGRAM_PASSWORD sur Railway")
        return
    
    bot_instance = SmartInstagramBot()
    
    # Tentative de connexion
    if bot_instance.safe_login():
        logger.info("✅ Bot initialisé avec succès")
        # Ici tu peux ajouter ta logique de follow/like
        # Pour l'instant, on garde juste le bot connecté
        while True:
            try:
                # Vérifier périodiquement la connexion
                bot_instance.cl.account_info()
                bot_instance.bot_status = "connected"
                time.sleep(300)  # 5 minutes
            except Exception as e:
                logger.warning("🔄 Reconnexion nécessaire...")
                bot_instance.safe_login()
                time.sleep(60)
    else:
        logger.error("❌ Impossible de connecter le bot")
        logger.info("💡 Vérifie tes identifiants et déverrouille ton compte Instagram")

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
                    <h2>Status: Initialisation en cours...</h2>
                    <p>Le bot est en cours de démarrage.</p>
                </div>
                <p><a href="/health">Health Check</a> | <a href="/status">Status Complet</a></p>
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
                <p><strong>Utilisateur configuré:</strong> {info['username_set']}</p>
                <p><strong>Dernière activité:</strong> {info['timestamp']}</p>
                <p><strong>Tentatives de connexion:</strong> {info['login_attempts']}</p>
                <p><strong>Dernière connexion:</strong> {info['last_login'] or 'Jamais'}</p>
                <p><strong>Erreur:</strong> {info['last_error'] or 'Aucune'}</p>
            </div>
            <p><a href="/health">Health Check</a> | <a href="/status">Status API</a> | <a href="/reconnect">Reconnecter</a></p>
        </body>
    </html>
    """

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy" if bot_instance else "initializing",
        "timestamp": datetime.now().isoformat(),
        "service": "instagram-bot"
    })

@app.route('/status')
def status():
    """Status complet du bot"""
    if bot_instance is None:
        return jsonify({"status": "not_initialized"})
    return jsonify(bot_instance.get_bot_info())

@app.route('/reconnect')
def reconnect():
    """Forcer la reconnexion"""
    if bot_instance is None:
        return jsonify({"error": "Bot non initialisé"})
    
    success = bot_instance.safe_login()
    return jsonify({
        "reconnected": success,
        "new_status": bot_instance.bot_status,
        "timestamp": datetime.now().isoformat()
    })

def start_server():
    """Démarrer le serveur en production"""
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🌐 Serveur démarré sur le port {port}")
    # Utiliser Waitress pour la production
    serve(app, host='0.0.0.0', port=port)

if __name__ == "__main__":
    # Démarrer le bot dans un thread séparé
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Démarrer le serveur web
    start_server()
