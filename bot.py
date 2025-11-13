from instagrapi import Client
from instagrapi.exceptions import LoginRequired
import logging
import time
import random
import json
import os
from datetime import datetime, timedelta

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
                "safety_score": 100
            }
    
    def save_analytics(self):
        with open(self.analytics_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def reset_daily_counts(self):
        if datetime.now().date() > datetime.fromisoformat(self.data["last_reset"]).date():
            self.data["daily_follows"] = 0
            self.data["daily_likes"] = 0
            self.data["daily_comments"] = 0
            self.data["last_reset"] = datetime.now().isoformat()
            self.save_analytics()
    
    def can_follow(self):
        self.reset_daily_counts()
        return self.data["daily_follows"] < random.randint(25, 40)
    
    def can_like(self):
        return self.data["daily_likes"] < random.randint(80, 120)
    
    def record_action(self, action_type):
        self.data[f"daily_{action_type}"] += 1
        self.save_analytics()

class SmartInstagramBot:
    def __init__(self):
        self.cl = Client()
        self.analytics = GrowthAnalytics()
        self.setup_safe_client()
        
    def setup_safe_client(self):
        """Configuration ultra-sécurisée"""
        self.cl.delay_range = [4, 12]  # Délais réalistes
        
        # Device settings réalistes
        self.cl.set_settings({
            "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
            "device_settings": {
                "app_version": "297.0.0.0.0",
                "android_version": 33,
                "android_release": "13.0",
                "dpi": "480dpi",
                "resolution": "1080x2310",
                "manufacturer": "Google",
                "device": "Pixel 7",
                "model": "Pixel 7",
            }
        })
    
    def safe_login(self):
        """Connexion sécurisée"""
        try:
            logger.info("🔐 Connexion sécurisée...")
            
            # Session existante
            if os.path.exists("session.json"):
                try:
                    self.cl.load_settings("session.json")
                    self.cl.get_timeline_feed()  # Test session
                    logger.info("✅ Session valide")
                    return True
                except LoginRequired:
                    logger.info("🔄 Session expirée")
            
            # Nouvelle connexion
            if self.cl.login(USERNAME, PASSWORD):
                logger.info("✅ Nouvelle connexion réussie")
                self.cl.dump_settings("session.json")
                return True
            
            logger.error("❌ Échec connexion")
            return False
            
        except Exception as e:
            logger.error(f"💥 Erreur connexion: {e}")
            return False
    
    def smart_delay(self, min_sec=15, max_sec=45):
        """Délai intelligent"""
        delay = random.randint(min_sec, max_sec)
        time.sleep(delay)
    
    def find_target_users(self):
        """Trouver des utilisateurs pertinents à suivre"""
        try:
            # Hashtags de niche (À ADAPTER)
            niches = ["digitalmarketing", "entrepreneur", "success", "motivation", "business"]
            target_hashtag = random.choice(niches)
            
            logger.info(f"🔍 Recherche hashtag: #{target_hashtag}")
            medias = self.cl.hashtag_medias_top(target_hashtag, amount=10)
            
            target_users = []
            for media in medias:
                user_id = media.user.pk
                user_info = self.cl.user_info(user_id)
                
                # Filtres de qualité
                if (user_info.follower_count < 50000 and 
                    user_info.follower_count > 1000 and
                    user_info.media_count > 10):
                    target_users.append(user_info)
            
            return target_users[:8]  # Limiter à 8 users
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche: {e}")
            return []
    
    def engage_with_user(self, user_info):
        """Interagir intelligemment avec un utilisateur"""
        try:
            logger.info(f"🎯 Interaction avec: {user_info.username}")
            
            # 1. Voir ses posts récents
            user_medias = self.cl.user_medias(user_info.pk, amount=3)
            
            # 2. Like 1-2 posts (pas tous)
            likes_done = 0
            for media in user_medias[:2]:
                if self.analytics.can_like():
                    self.cl.media_like(media.id)
                    self.analytics.record_action("likes")
                    likes_done += 1
                    logger.info(f"❤️ Like post {media.id}")
                    self.smart_delay(8, 20)
            
            # 3. Follow (seulement si conditions remplies)
            if (likes_done >= 1 and 
                self.analytics.can_follow() and 
                not self.cl.user_friendship(user_info.pk).following):
                
                self.cl.user_follow(user_info.pk)
                self.analytics.record_action("follows")
                logger.info(f"👤 Follow: {user_info.username}")
                
                # Commentaire occasionnel (10% du temps)
                if random.random() < 0.1 and user_medias:
                    comments = [
                        "Super contenu! 👍",
                        "Très intéressant!",
                        "J'aime ta démarche!",
                        "Continue comme ça! 👏"
                    ]
                    self.cl.media_comment(user_medias[0].id, random.choice(comments))
                    self.analytics.record_action("comments")
                    logger.info("💬 Commentaire ajouté")
            
            self.smart_delay(20, 40)
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur interaction: {e}")
            return False
    
    def strategic_unfollow(self):
        """Unfollow stratégique des non-reciproques"""
        try:
            if random.random() < 0.3:  # 30% de chance d'unfollow session
                logger.info("🔄 Vérification unfollow...")
                
                my_id = self.cl.user_id_from_username(USERNAME)
                following = self.cl.user_following(my_id)
                followers = self.cl.user_followers(my_id)
                
                followers_set = set(followers.keys())
                unfollow_count = 0
                
                for user_id in list(following.keys())[:15]:  # Limiter
                    if user_id not in followers_set:
                        # Attendre 4-7 jours avant unfollow
                        self.cl.user_unfollow(user_id)
                        unfollow_count += 1
                        logger.info(f"🚫 Unfollow non-réciproque")
                        self.smart_delay(25, 50)
                        if unfollow_count >= 5:  # Max 5 par session
                            break
                
                if unfollow_count > 0:
                    logger.info(f"📊 {unfollow_count} unfollows effectués")
                    
        except Exception as e:
            logger.error(f"❌ Erreur unfollow: {e}")
    
    def daily_growth_session(self):
        """Session de croissance quotidienne"""
        logger.info("🌱 Début session croissance")
        
        # 1. Activités organiques
        target_users = self.find_target_users()
        
        # 2. Interactions limitées
        interactions = 0
        for user in target_users:
            if interactions >= random.randint(3, 6):  # 3-6 interactions max
                break
                
            if self.engage_with_user(user):
                interactions += 1
        
        logger.info(f"📈 Session terminée: {interactions} interactions")
        
        # 3. Unfollow stratégique occasionnel
        self.strategic_unfollow()
        
        # 4. Analytics
        logger.info(f"📊 Aujourd'hui: {self.analytics.data['daily_follows']} follows, {self.analytics.data['daily_likes']} likes")

def main():
    logger.info("🚀 Bot Growth Sécurisé démarré")
    
    if not USERNAME or not PASSWORD:
        logger.error("❌ Configurer USERNAME/PASSWORD")
        return
    
    bot = SmartInstagramBot()
    
    if not bot.safe_login():
        logger.error("❌ Impossible de démarrer")
        return
    
    # Routine de croissance
    session_count = 0
    while session_count < 4:  # Max 4 sessions par jour
        try:
            session_count += 1
            logger.info(f"🔄 Session {session_count}/4")
            
            bot.daily_growth_session()
            
            # Pause stratégique entre sessions (2-4 heures)
            if session_count < 4:
                pause = random.randint(7200, 14400)  # 2-4 heures
                logger.info(f"💤 Prochaine session dans {pause//3600}h")
                time.sleep(pause)
                
        except Exception as e:
            logger.error(f"💥 Erreur session: {e}")
            time.sleep(1800)  # Attendre 30min
    
    logger.info("🎯 4 sessions quotidiennes terminées")

if __name__ == "__main__":
    main()
