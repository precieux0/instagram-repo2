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

# Configuration Flask
app = Flask(__name__)

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
                "daily_follows": 0,
                "daily_likes": 0,
                "daily_comments": 0,
                "total_followers": 0,
                "last_reset": datetime.now().isoformat(),
                "safety_score": 100,
                "bot_status": "running",
                "last_activity": datetime.now().isoformat(),
                "total_sessions": 0,
                "login_attempts": 0,
                "last_login": None
            }
    
    def save_analytics(self):
        self.data["last_activity"] = datetime.now().isoformat()
        with open(self.analytics_file, 'w') as f:
            json.dump(self.data, f, indent=2)

class SmartInstagramBot:
    def __init__(self):
        self.cl = Client()
        self.analytics = GrowthAnalytics()
        self.bot_status = "initializing"
        self.last_error = None
        self.setup_safe_client()
        
    def setup_safe_client(self):
        """Configuration ultra-sécurisée"""
        self.cl.delay_range = [7, 15]
        
        # Settings plus réalistes
        self.cl.set_settings({
            "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
            "device_settings": {
                "app_version": "320.0.0.0.0",
                "android_version": 34,
                "android_release": "14.0",
                "dpi": "480dpi",
                "resolution": "1080x2400",
                "manufacturer": "Samsung",
                "device": "SM-S901U",
                "model": "SM-S901U",
            }
        })
    
    def safe_login(self):
        """Connexion sécurisée avec gestion d'erreurs améliorée"""
        try:
            logger.info("🔐 Tentative de connexion sécurisée...")
            self.bot_status = "logging_in"
            self.analytics.data["login_attempts"] += 1
            self.analytics.save_analytics()
            
            # Supprimer la session existante si elle échoue
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
                except (LoginRequired, ChallengeRequired) as e:
                    logger.warning("🔄 Session expirée, nouvelle connexion...")
                    os.remove("session.json")
                except Exception as e:
                    logger.warning(f"🔄 Session corrompue: {e}")
                    os.remove("session.json")
            
            # Nouvelle connexion
            logger.info("🔄 Connexion avec identifiants...")
            
            # Ajouter un délai avant la connexion
            time.sleep(random.randint(5, 10))
            
            login_result = self.cl.login(USERNAME, PASSWORD)
            
            if login_result:
                logger.info("✅ Connexion réussie!")
                self.cl.dump_settings("session.json")
                self.bot_status = "connected"
                self.analytics.data["last_login"] = datetime.now().isoformat()
                self.analytics.save_analytics()
                return True
            else:
                logger.error("❌ Échec de la connexion")
                self.bot_status = "login_failed"
                return False
                
        except ChallengeRequired as e:
            logger.error("🔐 Challenge Instagram requis - Vérifie ton compte")
            self.last_error = "Challenge Instagram requis - Connecte-toi manuellement"
            self.bot_status = "challenge_required"
            return False
        except Exception as e:
            logger.error(f"💥 Erreur de connexion: {str(e)}")
            self.last_error = str(e)
            self.bot_status = "error"
            return False
    
    def get_bot_info(self):
        """Récupérer les infos du bot pour l'API"""
        return {
            "status": self.bot_status,
            "analytics": self.analytics.data,
            "last_error": self.last_error,
            "timestamp": datetime.now().isoformat(),
            "username": USERNAME if USERNAME else "non_configuré"
        }
    
    def try_reconnect(self):
        """Tenter de reconnecter le bot"""
        logger.info("🔄 Tentative de reconnexion...")
        time.sleep(60)  # Attendre 1 minute
        return self.safe_login()

# Instance globale du bot
bot_instance = None

def run_bot():
    """Fonction pour exécuter le bot en arrière-plan"""
    global bot_instance
    logger.info("🚀 Démarrage du Bot Instagram Growth")
    
    if not USERNAME or not PASSWORD:
        logger.error("❌ Variables d'environnement non configurées")
        logger.info("💡 Configure INSTAGRAM_USERNAME et INSTAGRAM_PASSWORD sur Railway")
        return
    
    bot_instance = SmartInstagramBot()
    
    # Tentative de connexion initiale
    if not bot_instance.safe_login():
        logger.error("❌ Échec de la connexion initiale")
        logger.info("💡 Vérifie tes identifiants et déverrouille ton compte Instagram")
        return
    
    logger.info("✅ Bot connecté avec succès!")
    
    # Simulation d'activité (remplace par ta logique réelle)
    while True:
        try:
            bot_instance.bot_status = "en_veille"
            logger.info("🤖 Bot en fonctionnement...")
            
            # Ici tu peux ajouter ta logique de follow/like
            # Pour l'instant, on simule juste un bot actif
            
            time.sleep(300)  # Attendre 5 minutes
            
            # Vérifier périodiquement la connexion
            if random.random() < 0.1:  # 10% de chance
                try:
                    bot_instance.cl.account_info()
                    bot_instance.bot_status = "connecté"
                except:
                    logger.warning("🔄 Reconnexion nécessaire...")
                    bot_instance.try_reconnect()
                    
        except Exception as e:
            logger.error(f"💥 Erreur dans la boucle principale: {e}")
            bot_instance.last_error = str(e)
            bot_instance.bot_status = "error"
            time.sleep(60)

# Routes Flask pour le monitoring
@app.route('/')
def dashboard():
    """Page d'accueil du dashboard"""
    if bot_instance is None:
        return """
        <html>
            <head><title>Instagram Bot</title></head>
            <body>
                <h1>🤖 Bot Instagram Growth</h1>
                <p>Bot en cours d'initialisation...</p>
                <p><a href="/health">Vérifier la santé</a></p>
            </body>
        </html>
        """
    
    info = bot_instance.get_bot_info()
    return f"""
    <html>
        <head><title>Instagram Bot Status</title></head>
        <body>
            <h1>🤖 Bot Instagram Growth</h1>
            <div style="padding: 20px; background: #f5f5f5; border-radius: 10px;">
                <h2>Status: {info['status']}</h2>
                <p><strong>Utilisateur:</strong> {info['username']}</p>
                <p><strong>Dernière activité:</strong> {info['timestamp']}</p>
                <p><strong>Erreur:</strong> {info['last_error'] or 'Aucune'}</p>
                <p><strong>Tentatives de connexion:</strong> {info['analytics']['login_attempts']}</p>
            </div>
            <p><a href="/health">Health Check</a> | <a href="/analytics">Analytics</a></p>
        </body>
    </html>
    """

@app.route('/health')
def health_check():
    """Endpoint de santé"""
    if bot_instance is None:
        return jsonify({"status": "initializing", "message": "Bot en cours de démarrage"})
    
    return jsonify(bot_instance.get_bot_info())

@app.route('/analytics')
def analytics():
    """Endpoint des analytics"""
    if bot_instance is None:
        return jsonify({"error": "Bot non initialisé"})
    
    return jsonify(bot_instance.analytics.data)

@app.route('/reconnect')
def reconnect():
    """Forcer la reconnexion"""
    if bot_instance is None:
        return jsonify({"error": "Bot non initialisé"})
    
    success = bot_instance.try_reconnect()
    return jsonify({"reconnect_attempt": success, "new_status": bot_instance.bot_status})

def start_flask():
    """Démarrer le serveur Flask"""
    port = int(os.environ.get("PORT", 8080))
    # DÉSACTIVER le mode debug pour production
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    # Démarrer le bot dans un thread séparé
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Démarrer le serveur Flask
    logger.info("🌐 Démarrage du serveur de monitoring sur le port 8080...")
    start_flask()
