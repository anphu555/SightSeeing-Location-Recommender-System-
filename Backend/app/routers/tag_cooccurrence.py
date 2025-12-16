"""
Tag Co-occurrence Mining
Phân tích tags nào thường xuất hiện cùng nhau trong preferences của users
"""

import numpy as np
from collections import defaultdict, Counter
from sqlmodel import Session, select
from typing import Dict, List, Tuple
import pickle
import os

from app.schemas import Rating, Place, User

class TagCooccurrence:
    """Mine tag co-occurrence patterns từ user interactions"""
    
    def __init__(self):
        self.tag_cooccurrence = defaultdict(Counter)  # tag -> {related_tag: count}
        self.tag_similarity = {}  # (tag1, tag2) -> similarity_score
        self.all_tags = set()
        
    def build_from_database(self, session: Session, min_score=4.0):
        """
        Build co-occurrence matrix từ user ratings
        Logic: Nếu user rate cao 2 places có tag A và tag B → A và B related
        """
        print("Building tag co-occurrence matrix...")
        
        # Get all users
        users = session.exec(select(User)).all()
        
        for user in users:
            # Get places user liked (score >= min_score)
            ratings = session.exec(
                select(Rating).where(
                    Rating.user_id == user.id,
                    Rating.score >= min_score
                )
            ).all()
            
            # Collect tags from liked places
            user_tags = []
            for rating in ratings:
                place = session.get(Place, rating.place_id)
                if place and place.tags:
                    user_tags.extend(place.tags)
                    self.all_tags.update(place.tags)
            
            # Count co-occurrences
            # If user likes both tag A and tag B, increment co-occurrence
            unique_tags = list(set(user_tags))
            
            for i, tag_a in enumerate(unique_tags):
                for tag_b in unique_tags[i+1:]:
                    self.tag_cooccurrence[tag_a][tag_b] += 1
                    self.tag_cooccurrence[tag_b][tag_a] += 1
        
        # Calculate similarity scores (Jaccard-like)
        print(f"Calculating similarity for {len(self.all_tags)} unique tags...")
        
        for tag_a in self.all_tags:
            for tag_b in self.all_tags:
                if tag_a >= tag_b:  # Avoid duplicates
                    continue
                
                cooccur_count = self.tag_cooccurrence[tag_a][tag_b]
                
                if cooccur_count > 0:
                    # Normalize by total occurrences
                    total_a = sum(self.tag_cooccurrence[tag_a].values())
                    total_b = sum(self.tag_cooccurrence[tag_b].values())
                    
                    # Jaccard-like similarity
                    similarity = cooccur_count / (total_a + total_b - cooccur_count + 1)
                    
                    self.tag_similarity[(tag_a, tag_b)] = similarity
                    self.tag_similarity[(tag_b, tag_a)] = similarity
        
        print(f"✓ Found {len(self.tag_similarity)} tag relationships")
        
    def get_related_tags(self, tag: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Lấy top-K tags liên quan nhất đến tag cho trước"""
        related = []
        
        for other_tag in self.all_tags:
            if other_tag == tag:
                continue
            
            key = (tag, other_tag)
            if key in self.tag_similarity:
                related.append((other_tag, self.tag_similarity[key]))
        
        # Sort by similarity
        related.sort(key=lambda x: x[1], reverse=True)
        return related[:top_k]
    
    def expand_query_tags(self, tags: List[str], expansion_factor: int = 2) -> List[str]:
        """
        Query expansion: Thêm related tags vào query
        tags: original user tags
        expansion_factor: số lượng related tags thêm vào cho mỗi original tag
        """
        expanded = set(tags)
        
        for tag in tags:
            related = self.get_related_tags(tag, top_k=expansion_factor)
            for related_tag, similarity in related:
                if similarity > 0.1:  # Threshold
                    expanded.add(related_tag)
        
        return list(expanded)
    
    def get_tag_boost_scores(self, user_tags: List[str]) -> Dict[str, float]:
        """
        Tính boost scores cho tất cả tags dựa trên user_tags
        Return: {tag: boost_score}
        """
        boost_scores = defaultdict(float)
        
        for user_tag in user_tags:
            # Original tag gets highest boost
            boost_scores[user_tag] += 1.0
            
            # Related tags get proportional boost
            related = self.get_related_tags(user_tag, top_k=10)
            for related_tag, similarity in related:
                boost_scores[related_tag] += similarity * 0.5  # 50% of similarity
        
        return dict(boost_scores)
    
    def save(self, filepath: str):
        """Save to disk"""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'tag_cooccurrence': dict(self.tag_cooccurrence),
                'tag_similarity': self.tag_similarity,
                'all_tags': self.all_tags
            }, f)
        print(f"✓ Saved tag co-occurrence to {filepath}")
    
    def load(self, filepath: str):
        """Load from disk"""
        if not os.path.exists(filepath):
            return False
        
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.tag_cooccurrence = defaultdict(Counter, data['tag_cooccurrence'])
            self.tag_similarity = data['tag_similarity']
            self.all_tags = data['all_tags']
        
        print(f"✓ Loaded tag co-occurrence from {filepath}")
        return True


# Global instance
tag_cooccurrence = TagCooccurrence()


def initialize_tag_cooccurrence(session: Session, cache_file: str = "tag_cooccurrence.pkl"):
    """Initialize tag co-occurrence (load from cache or build)"""
    global tag_cooccurrence
    
    # Try to load from cache
    if tag_cooccurrence.load(cache_file):
        return tag_cooccurrence
    
    # Build from scratch
    tag_cooccurrence.build_from_database(session)
    tag_cooccurrence.save(cache_file)
    
    return tag_cooccurrence


if __name__ == "__main__":
    from app.database import engine
    
    session = Session(engine)
    
    # Build tag co-occurrence
    tc = TagCooccurrence()
    tc.build_from_database(session)
    tc.save("tag_cooccurrence.pkl")
    
    # Test
    print("\n=== EXAMPLES ===\n")
    
    test_tags = ["Beach", "Historical", "Nature", "Food"]
    
    for tag in test_tags:
        related = tc.get_related_tags(tag, top_k=5)
        print(f"{tag}:")
        for rel_tag, sim in related:
            print(f"  → {rel_tag} (similarity: {sim:.3f})")
        print()
    
    # Query expansion example
    print("Query expansion example:")
    original = ["Beach", "Seafood"]
    expanded = tc.expand_query_tags(original, expansion_factor=3)
    print(f"Original: {original}")
    print(f"Expanded: {expanded}")
