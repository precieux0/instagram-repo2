from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
import logging
import time
import random
import json
import os
from datetime import datetime
from flask import Flask, jsonify
import threading
from waitress import serve

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

USERNAME = os.getenv('INSTAGRAM_USERNAME')
PASSWORD = os.getenv('INSTAGRAM_PASSWORD')

class InstagramBotManager:
    def __init__(self):
        self.client = Client()
        self.bot_status = "initializing"
        self.last_error = None
        self.login_attempts = 0
        self.last_login = None
        
    def get_realistic_settings(self):
        """Settings très réalistes pour éviter la détection"""
        return {
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
                "cpu": "qcom",
                "version_code": "314665256"
            },
            "country": "US",
            "locale": "en_US",
            "timezone_offset": -28800,
            "radio_type": "wifi-none",
            "connection_type": "WIFI",
            "capabilities": "3brTvwE="
        }
    
    def advanced_login(self):
        """Méthode de connexion avancée avec contournements"""
        try:
            self.login_attempts += 1
            logger.info(f"🔐 Tentative de connexion #{self.login_attempts}")
            self.bot_status = "logging_in"
            
            # Configuration réaliste
            settings = self.get_realistic_settings()
            self.client.set_settings(settings)
            self.client.delay_range = [10, 25]
            
            # Supprimer session problématique
            if os.path.exists("session.json"):
                try:
                    self.client.load_settings("session.json")
                    # Tester la session
                    user_info = self.client.account_info()
                    logger.info(f"✅ Session valide: {user_info.username}")
                    self.bot_status = "connected"
                    self.last_login = datetime.now().isoformat()
                    return True
                except Exception as e:
                    logger.warning(f"🔄 Session invalide: {e}")
                    if os.path.exists("session.json"):
                        os.remove("session.json")
            
            # Nouvelle connexion avec approche différente
            logger.info("🔄 Nouvelle connexion avec identifiants...")
            
            # Délai aléatoire avant connexion
            delay = random.uniform(8, 20)
            time.sleep(delay)
            
            # Méthode de connexion alternative
            login_success = self.client.login(USERNAME, PASSWORD, relogin=True)
            
            if login_success:
                logger.info("✅ Connexion réussie!")
                self.client.dump_settings("session.json")
                self.bot_status = "connected"
                self.last_login = datetime.now().isoformat()
                return True
            else:
                logger.error("❌ Échec de la connexion")
                self.bot_status = "login_failed"
                return False
                
        except ChallengeRequired as e:
            error_msg = "🔐 Challenge de sécurité Instagram détecté - Connecte-toi manuellement sur instagram.com"
            logger.error(error_msg)
            self.last_error = error_msg
            self.bot_status = "challenge_required"
            return False
            
        except Exception as e:
            error_msg = f"Erreur de connexion: {str(e)}"
            logger.error(f"💥 {error_msg}")
            self.last_error = error_msg
            self.bot_status = "error"
            return False
    
    def get_bot_info(self):
        return {
            "status": self.bot_status,
            "login_attempts": self.login_attempts,
            "last_login": self.last_login,
            "last_error": self.last_error,
            "timestamp": datetime.now().isoformat(),
            "username": USERNAME,
            "platform": "Railway",
            "message": "Instagram Growth Bot"
        }

# Instance globale
bot_manager = None

def bot_worker():
    """Tâche en arrière-plan pour le bot"""
    global bot_manager
    logger.info("🚀 Initialisation du Bot Instagram")
    
    if not USERNAME or not PASSWORD:
        logger.error("❌ Identifiants non configurés")
        return
    
    bot_manager = InstagramBotManager()
    
    # Tentative de connexion initiale
    if bot_manager.advanced_login():
        logger.info("🎉 Bot prêt et connecté!")
        
        # Boucle de maintien de connexion
        while True:
            try:
                # Vérifier périodiquement la connexion
                if bot_manager.bot_status == "connected":
                    account_info = bot_manager.client.account_info()
                    logger.info(f"📊 Statut: {account_info.username} - {account_info.follower_count} followers")
                
                # Attendre avant prochaine vérification
                time.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.warning(f"🔄 Problème de connexion: {e}")
                bot_manager.advanced_login()
                time.sleep(60)
    else:
        logger.error("❌ Impossible de connecter le bot")
        logger.info("""
        💡 SOLUTIONS RECOMMANDÉES:
        1. Connecte-toi MANUELLEMENT à Instagram avec del.una99
        2. Vérifie qu'il n'y a pas de blocage de sécurité
        3. Réessaie dans 1-2 heures
        4. Utilise un compte Instagram moins récent ou plus actif
        """)

# Application Web
app = Flask(__name__)

@app.route('/')
def dashboard():
    """Tableau de bord principal"""
    if bot_manager is None:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Instagram Bot - Railway</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .status { padding: 20px; border-radius: 8px; margin: 20px 0; }
                .connected { background: #d4edda; border: 1px solid #c3e6cb; }
                .error { background: #f8d7da; border: 1px solid #f5c6cb; }
                .warning { background: #fff3cd; border: 1px solid #ffeaa7; }
                .info { background: #d1ecf1; border: 1px solid #bee5eb; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 Bot Instagram Growth</h1>
                <div class="status info">
                    <h2>🔄 Initialisation en cours...</h2>
                    <p>Le bot est en cours de démarrage.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    info = bot_manager.get_bot_info()
    
    # Déterminer la classe CSS selon le statut
    status_class = {
        "connected": "connected",
        "error": "error", 
        "login_failed": "warning",
        "challenge_required": "warning",
        "logging_in": "info"
    }.get(info['status'], 'info')
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Instagram Bot - Railway</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .status {{ padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .connected {{ background: #d4edda; border: 1px solid #c3e6cb; }}
            .error {{ background: #f8d7da; border: 1px solid #f5c6cb; }}
            .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; }}
            .info {{ background: #d1ecf1; border: 1px solid #bee5eb; }}
            .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }}
            .info-item {{ padding: 10px; background: #f8f9fa; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Bot Instagram Growth</h1>
            
            <div class="status {status_class}">
                <h2>Status: {info['status'].upper()}</h2>
                <div class="info-grid">
                    <div class="info-item">
                        <strong>Utilisateur:</strong><br>{info['username']}
                    </div>
                    <div class="info-item">
                        <strong>Tentatives:</strong><br>{info['login_attempts']}
                    </div>
                    <div class="info-item">
                        <strong>Dernière connexion:</strong><br>{info['last_login'] or 'Jamais'}
                    </div>
                    <div class="info-item">
                        <strong>Platform:</strong><br>{info['platform']}
                    </div>
                </div>
                <p><strong>Dernière erreur:</strong> {info['last_error'] or 'Aucune'}</p>
            </div>
            
            <div class="status info">
                <h3>💡 Instructions de dépannage</h3>
                <p>Si le bot ne se connecte pas:</p>
                <ol>
                    <li>Va sur <a href="https://instagram.com" target="_blank">instagram.com</a></li>
                    <li>Connecte-toi avec <strong>del.una99</strong></li>
                    <li>Accepte tous les challenges de sécurité</li>
                    <li>Attends 10 minutes puis rafraîchis cette page</li>
                </ol>
                <p><a href="/reconnect" style="background: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">🔄 Forcer la reconnexion</a></p>
            </div>
            
            <p>
                <a href="/health">Health Check</a> | 
                <a href="/status">API Status</a> |
                <a href="/logs">Derniers logs</a>
            </p>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "instagram-bot",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/status')
def status():
    if bot_manager is None:
        return jsonify({"status": "initializing"})
    return jsonify(bot_manager.get_bot_info())

@app.route('/reconnect')
def reconnect():
    if bot_manager:
        success = bot_manager.advanced_login()
        return jsonify({
            "reconnect_attempted": True,
            "success": success,
            "new_status": bot_manager.bot_status
        })
    return jsonify({"error": "Bot non initialisé"})

@app.route('/logs')
def show_logs():
    return jsonify({
        "message": "Logs disponibles dans l'interface Railway",
        "timestamp": datetime.now().isoformat()
    })

def start_web_server():
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🌐 Serveur web démarré sur le port {port}")
    serve(app, host='0.0.0.0', port=port)

if __name__ == "__main__":
    # Démarrer le bot dans un thread séparé
    bot_thread = threading.Thread(target=bot_worker, daemon=True)
    bot_thread.start()
    
    # Démarrer le serveur web
    start_web_server()
