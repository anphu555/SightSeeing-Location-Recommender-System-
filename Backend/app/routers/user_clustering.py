"""
User Clustering
Nhóm users có preferences tương tự để improve collaborative filtering
"""

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from collections import defaultdict
from sqlmodel import Session, select
from typing import Dict, List
import pickle
import os

from app.schemas import Rating, Place, User

class UserClusterer:
    """Cluster users based on their preference patterns"""
    
    def __init__(self, n_clusters: int = 5):
        self.n_clusters = n_clusters
        self.kmeans = None
        self.scaler = StandardScaler()
        self.user_features = {}  # user_id -> feature_vector
        self.user_clusters = {}  # user_id -> cluster_id
        self.cluster_profiles = {}  # cluster_id -> popular_tags
        self.all_tags = []
        
    def build_user_features(self, session: Session):
        """
        Build feature vectors cho mỗi user
        Features: TF-IDF style vector của tags từ rated places
        """
        print("Building user feature vectors...")
        
        # Get all unique tags
        places = session.exec(select(Place)).all()
        tag_set = set()
        for place in places:
            if place.tags:
                tag_set.update(place.tags)
        
        self.all_tags = sorted(list(tag_set))
        tag_to_idx = {tag: idx for idx, tag in enumerate(self.all_tags)}
        
        # Build feature vector for each user
        users = session.exec(select(User)).all()
        
        for user in users:
            # Get user's high-rated places
            ratings = session.exec(
                select(Rating).where(
                    Rating.user_id == user.id,
                    Rating.score >= 3.0
                )
            ).all()
            
            # Count tag frequencies
            tag_counts = defaultdict(float)
            total_weight = 0.0
            
            for rating in ratings:
                place = session.get(Place, rating.place_id)
                if place and place.tags:
                    # Weight by rating score
                    weight = 2 ** (rating.score - 3.0)  # Exponential
                    
                    for tag in place.tags:
                        tag_counts[tag] += weight
                    total_weight += weight
            
            # Normalize
            if total_weight > 0:
                for tag in tag_counts:
                    tag_counts[tag] /= total_weight
            
            # Create feature vector
            feature_vec = np.zeros(len(self.all_tags))
            for tag, count in tag_counts.items():
                if tag in tag_to_idx:
                    feature_vec[tag_to_idx[tag]] = count
            
            self.user_features[user.id] = feature_vec
        
        print(f"✓ Built feature vectors for {len(self.user_features)} users")
        print(f"✓ Feature dimension: {len(self.all_tags)}")
    
    def fit(self, session: Session):
        """Cluster users"""
        # Build features
        self.build_user_features(session)
        
        if len(self.user_features) < self.n_clusters:
            print(f"⚠️ Not enough users ({len(self.user_features)}) for {self.n_clusters} clusters")
            self.n_clusters = max(2, len(self.user_features) // 2)
            print(f"  Reducing to {self.n_clusters} clusters")
        
        # Prepare data
        user_ids = list(self.user_features.keys())
        X = np.array([self.user_features[uid] for uid in user_ids])
        
        # Normalize
        X_scaled = self.scaler.fit_transform(X)
        
        # Cluster
        print(f"Clustering {len(user_ids)} users into {self.n_clusters} clusters...")
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        cluster_labels = self.kmeans.fit_predict(X_scaled)
        
        # Map user_id to cluster
        for user_id, cluster_id in zip(user_ids, cluster_labels):
            self.user_clusters[user_id] = int(cluster_id)
        
        # Build cluster profiles
        self._build_cluster_profiles(session)
        
        print(f"✓ Clustering complete!")
        self._print_cluster_stats()
    
    def _build_cluster_profiles(self, session: Session):
        """Build tag profiles for each cluster"""
        # Group users by cluster
        cluster_users = defaultdict(list)
        for user_id, cluster_id in self.user_clusters.items():
            cluster_users[cluster_id].append(user_id)
        
        # For each cluster, find popular tags
        for cluster_id, user_ids in cluster_users.items():
            tag_scores = defaultdict(float)
            
            for user_id in user_ids:
                ratings = session.exec(
                    select(Rating).where(
                        Rating.user_id == user_id,
                        Rating.score >= 4.0
                    )
                ).all()
                
                for rating in ratings:
                    place = session.get(Place, rating.place_id)
                    if place and place.tags:
                        for tag in place.tags:
                            tag_scores[tag] += rating.score
            
            # Normalize and get top tags
            if tag_scores:
                max_score = max(tag_scores.values())
                tag_scores = {tag: score / max_score for tag, score in tag_scores.items()}
            
            # Sort and store top 10
            top_tags = sorted(tag_scores.items(), key=lambda x: x[1], reverse=True)[:10]
            self.cluster_profiles[cluster_id] = top_tags
    
    def _print_cluster_stats(self):
        """Print cluster statistics"""
        print("\n=== CLUSTER STATISTICS ===\n")
        
        cluster_sizes = defaultdict(int)
        for cluster_id in self.user_clusters.values():
            cluster_sizes[cluster_id] += 1
        
        for cluster_id in sorted(cluster_sizes.keys()):
            size = cluster_sizes[cluster_id]
            print(f"Cluster {cluster_id}: {size} users")
            
            if cluster_id in self.cluster_profiles:
                top_tags = self.cluster_profiles[cluster_id][:5]
                tags_str = ", ".join([f"{tag}({score:.2f})" for tag, score in top_tags])
                print(f"  Top tags: {tags_str}")
            print()
    
    def get_user_cluster(self, user_id: int) -> int:
        """Get cluster ID for user"""
        return self.user_clusters.get(user_id, -1)
    
    def get_cluster_recommendations(self, user_id: int, session: Session, top_k: int = 20) -> List[int]:
        """
        Get popular places from user's cluster
        """
        cluster_id = self.get_user_cluster(user_id)
        
        if cluster_id == -1:
            return []
        
        # Get cluster profile tags
        if cluster_id not in self.cluster_profiles:
            return []
        
        cluster_tags = [tag for tag, score in self.cluster_profiles[cluster_id]]
        
        # Find places with these tags
        places = session.exec(select(Place)).all()
        
        place_scores = []
        for place in places:
            if not place.tags:
                continue
            
            # Score based on tag overlap with cluster profile
            score = 0.0
            for tag in place.tags:
                # Find tag in cluster profile
                for i, (cluster_tag, cluster_score) in enumerate(self.cluster_profiles[cluster_id]):
                    if tag == cluster_tag:
                        # Weight by position in cluster profile
                        position_weight = 1.0 - (i / len(self.cluster_profiles[cluster_id]))
                        score += cluster_score * position_weight
                        break
            
            if score > 0:
                place_scores.append((place.id, score))
        
        # Sort and return top-K
        place_scores.sort(key=lambda x: x[1], reverse=True)
        return [place_id for place_id, score in place_scores[:top_k]]
    
    def save(self, filepath: str):
        """Save to disk"""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'n_clusters': self.n_clusters,
                'kmeans': self.kmeans,
                'scaler': self.scaler,
                'user_features': self.user_features,
                'user_clusters': self.user_clusters,
                'cluster_profiles': self.cluster_profiles,
                'all_tags': self.all_tags
            }, f)
        print(f"✓ Saved user clustering to {filepath}")
    
    def load(self, filepath: str):
        """Load from disk"""
        if not os.path.exists(filepath):
            return False
        
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.n_clusters = data['n_clusters']
            self.kmeans = data['kmeans']
            self.scaler = data['scaler']
            self.user_features = data['user_features']
            self.user_clusters = data['user_clusters']
            self.cluster_profiles = data['cluster_profiles']
            self.all_tags = data['all_tags']
        
        print(f"✓ Loaded user clustering from {filepath}")
        return True


# Global instance
user_clusterer = UserClusterer(n_clusters=5)


def initialize_user_clustering(session: Session, cache_file: str = "user_clustering.pkl"):
    """Initialize user clustering (load from cache or build)"""
    global user_clusterer
    
    # Try to load from cache
    if user_clusterer.load(cache_file):
        return user_clusterer
    
    # Build from scratch
    user_clusterer.fit(session)
    user_clusterer.save(cache_file)
    
    return user_clusterer


if __name__ == "__main__":
    from app.database import engine
    
    session = Session(engine)
    
    # Build user clustering
    uc = UserClusterer(n_clusters=5)
    uc.fit(session)
    uc.save("user_clustering.pkl")
    
    # Test
    print("\n=== TEST CLUSTER RECOMMENDATIONS ===\n")
    
    users = session.exec(select(User)).all()
    test_user = users[0] if users else None
    
    if test_user:
        cluster_id = uc.get_user_cluster(test_user.id)
        print(f"User {test_user.id} is in cluster {cluster_id}")
        
        recs = uc.get_cluster_recommendations(test_user.id, session, top_k=5)
        print(f"Top 5 cluster recommendations: {recs}")
